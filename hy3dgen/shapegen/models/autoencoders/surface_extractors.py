# Hunyuan 3D is licensed under the TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT
# except for the third-party components listed below.
# Hunyuan 3D does not impose any additional limitations beyond what is outlined
# in the repsective licenses of these third-party components.
# Users must comply with all terms and conditions of original licenses of these third-party
# components and must ensure that the usage of the third party components adheres to
# all relevant laws and regulations.

# For avoidance of doubts, Hunyuan 3D means the large language models and
# their software and algorithms, including trained model weights, parameters (including
# optimizer states), machine-learning model code, inference-enabling code, training-enabling code,
# fine-tuning enabling code and other elements of the foregoing made publicly available
# by Tencent in accordance with TENCENT HUNYUAN COMMUNITY LICENSE AGREEMENT.

from typing import Union, Tuple, List
import logging

import numpy as np
import torch
from skimage import measure

logger = logging.getLogger(__name__)


class Latent2MeshOutput:

    def __init__(self, mesh_v=None, mesh_f=None):
        self.mesh_v = mesh_v
        self.mesh_f = mesh_f


def center_vertices(vertices):
    """Translate the vertices so that bounding box is centered at zero."""
    vert_min = vertices.min(dim=0)[0]
    vert_max = vertices.max(dim=0)[0]
    vert_center = 0.5 * (vert_min + vert_max)
    return vertices - vert_center


class SurfaceExtractor:
    def _compute_box_stat(self, bounds: Union[Tuple[float], List[float], float], octree_resolution: int):
        if isinstance(bounds, float):
            bounds = [-bounds, -bounds, -bounds, bounds, bounds, bounds]

        bbox_min, bbox_max = np.array(bounds[0:3]), np.array(bounds[3:6])
        bbox_size = bbox_max - bbox_min
        grid_size = [int(octree_resolution) + 1, int(octree_resolution) + 1, int(octree_resolution) + 1]
        return grid_size, bbox_min, bbox_size

    def run(self, *args, **kwargs):
        return NotImplementedError

    def __call__(self, grid_logits, **kwargs):
        outputs = []
        for i in range(grid_logits.shape[0]):
            try:
                vertices, faces = self.run(grid_logits[i], **kwargs)
                vertices = vertices.astype(np.float32)
                faces = np.ascontiguousarray(faces)
                outputs.append(Latent2MeshOutput(mesh_v=vertices, mesh_f=faces))

            except Exception:
                import traceback
                traceback.print_exc()
                outputs.append(None)

        return outputs


class MCSurfaceExtractor(SurfaceExtractor):
    def run(self, grid_logit, *, mc_level, bounds, octree_resolution, **kwargs):
        vertices, faces, normals, _ = measure.marching_cubes(
            grid_logit.cpu().numpy(),
            mc_level,
            method="lewiner"
        )
        grid_size, bbox_min, bbox_size = self._compute_box_stat(bounds, octree_resolution)
        vertices = vertices / grid_size * bbox_size + bbox_min
        return vertices, faces


class DMCSurfaceExtractor(SurfaceExtractor):
    def __init__(self):
        super().__init__()
        self._use_fallback = False
        
    def run(self, grid_logit, *, octree_resolution, **kwargs):
        device = grid_logit.device
        
        # Try to use diso if available (only check once)
        if not hasattr(self, 'dmc') and not self._use_fallback:
            try:
                from diso import DiffDMC
                self.dmc = DiffDMC(dtype=torch.float32).to(device)
            except ImportError:
                # diso module not installed - fall back to standard MC
                import warnings
                warnings.warn(
                    "diso module not found. Falling back to standard marching cubes. "
                    "For better quality, install diso via `pip install diso`.",
                    UserWarning
                )
                self._use_fallback = True
                self._fallback_extractor = MCSurfaceExtractor()
            except (RuntimeError, ValueError, TypeError, AttributeError) as e:
                # diso initialization failed - fall back to standard MC
                import warnings
                warnings.warn(
                    f"Failed to initialize diso ({type(e).__name__}: {e}). "
                    "Falling back to standard marching cubes.",
                    UserWarning
                )
                logger.debug(f"diso initialization error: {e}", exc_info=True)
                self._use_fallback = True
                self._fallback_extractor = MCSurfaceExtractor()
        
        # Use fallback if diso is not available
        if self._use_fallback:
            return self._fallback_extractor.run(grid_logit, octree_resolution=octree_resolution, **kwargs)
        
        # Use diso if available
        sdf = -grid_logit / octree_resolution
        sdf = sdf.to(torch.float32).contiguous()
        verts, faces = self.dmc(sdf, deform=None, return_quads=False, normalize=True)
        verts = center_vertices(verts)
        vertices = verts.detach().cpu().numpy()
        faces = faces.detach().cpu().numpy()[:, ::-1]
        return vertices, faces


SurfaceExtractors = {
    'mc': MCSurfaceExtractor,
    'dmc': DMCSurfaceExtractor,
}
