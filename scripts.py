import io
import nibabel as nib
import numpy as np
from skimage import measure

import pyodide_js
from pyodide.http import pyfetch

async def download_file(url, fname="data.nii"):
    response = await pyfetch(url)
    
    if response.status == 200:
        # Save to virtual file system
        with open(fname, "wb") as f:
            f.write(await response.bytes())

def load_nii(fname="data.nii"):
    ni_img = nib.load(fname)
    data = ni_img.get_fdata()

    header = ni_img.header
    # dimension of each voxel
    header.get_zooms()
    # convert mm to m
    dv = [d / 1000.0 for d in header.get_zooms()]

    return data, dv

async def load_nii_direct(url):
    '''
    fetch a .nii file by url and load it directly in python environment
    '''
    response = await pyfetch(url)
    
    image_bytes = None
    if response.status == 200:
        image_bytes = await response.bytes()
    else:
        return None

    # load file from raw bytes
    ni_img = nib.Nifti1Image.from_bytes(image_bytes)
    header = ni_img.header
    data = ni_img.get_fdata()
    # dimension of each voxel in mm
    dv = header.get_zooms()

    return data, dv

def marching_cubes_voxels(data, dv, level):
    '''
    run marching cubes algo from a data array that is a medical image
    data: 3D array, the voxels data with density
    dv: (float, float, float), dimension of each voxel as read from the source file
    level: float, density isovalue to render the survace with
    '''
    # scikit-image measure.marching_cubes returns normals by default
    verts, faces, normals, values = measure.marching_cubes(data, level=level)
    # convert vertices to physical unit (bohr) fom array indices
    verts[:, 0] = (verts[:, 0] * dv[0]) - data.shape[0] * dv[0] / 2
    verts[:, 1] = (verts[:, 1] * dv[1]) - data.shape[1] * dv[1] / 2
    verts[:, 2] = (verts[:, 2] * dv[2]) - data.shape[2] * dv[2] / 2
    # print('num_verts: ', verts.shape[0])
    # print('num_faces: ', faces.shape[0])
    return marching_cubes_res_to_obj(verts, faces, normals)

# OBJ writer that include the 'vn' (vertex normal) data
def marching_cubes_res_to_obj(verts, faces, normals):
    sio = io.StringIO()
    # vertices
    np.savetxt(sio, verts, fmt='v %.6f %.6f %.6f')
    # vertex normals
    np.savetxt(sio, normals, fmt='vn %.6f %.6f %.6f')
    # faces referencing both vertices and normals (1-indexed)
    faces_p1 = faces + 1
    np.savetxt(sio, faces_p1, fmt='f %d %d %d')

    res = sio.getvalue()
    sio.close()
    
    return res

def build_isosurface_range(data, dv, dens_range):
    '''
    apply marching cubes algorithm by a range of HU lower and upper bound
    '''
    dens_min, dens_max = dens_range
    # for the max side
    verts_max, faces_max, normals_max, values_max = measure.marching_cubes(data, level=dens_max, gradient_direction="ascent")
    # convert vertices to physical unit (bohr) fom array indices
    verts_max[:, 0] = (verts_max[:, 0] * dv[0]) - data.shape[0] * dv[0] / 2
    verts_max[:, 1] = (verts_max[:, 1] * dv[1]) - data.shape[1] * dv[1] / 2
    verts_max[:, 2] = (verts_max[:, 2] * dv[2]) - data.shape[2] * dv[2] / 2
    # for the min side
    verts_min, faces_min, normals_min, values_min = measure.marching_cubes(data, level=dens_min, gradient_direction="descent")
    # convert vertices to physical unit (bohr) fom array indices
    verts_min[:, 0] = (verts_min[:, 0] * dv[0]) - data.shape[0] * dv[0] / 2
    verts_min[:, 1] = (verts_min[:, 1] * dv[1]) - data.shape[1] * dv[1] / 2
    verts_min[:, 2] = (verts_min[:, 2] * dv[2]) - data.shape[2] * dv[2] / 2

    # concatenate the two surfaces
    verts = np.concatenate([verts_max, verts_min])
    faces = np.concatenate([faces_max, faces_min])
    # normals are indices so we need to add the offset
    normals = np.concatenate([normals_max, normals_min + normals_max.shape[0]])

    res = marching_cubes_res_to_obj(verts, faces, normals)
    return res

loaded_model = ""

def avg_pool(arr, d):
    '''
    apply dxd average pool on 'horizontal' (horizontal when the person is standing up) 
    i.e. first 2, dimensions of the scan data array
    '''
    # original dimensions
    m, n, p = arr.shape
    arr = arr[:m - m % d, :n - n % d]
    # reshape by grouping 2x2 blocks, then average over those blocks
    return arr.reshape(m // d, d, n // d, d, p).mean(axis=(1, 3))

pool_factor = 2

# test code
async def test_load_scan_model(url):
    global loaded_model

    # await download_file(url)
    # data, dv = load_nii()
    data, dv = await load_nii_direct(url)

    # convert mm to m in voxel dimensions
    dv = [d / 1000.0 for d in dv]
    # then scale by pooling factor as well
    data = avg_pool(data, d=pool_factor)
    dv[0] *= pool_factor
    dv[1] *= pool_factor

    # threshold of 110 hounsfield units for bones
    level = 110
    res_obj = marching_cubes_voxels(data, dv, level)

    # HU range of (35, 75) for muscle
    # dens_range = (35, 75)
    # res_obj = build_isosurface_range(data, dv, dens_range)
    loaded_model = res_obj