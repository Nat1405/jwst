from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

from asdf import AsdfFile
from astropy import coordinates as coord
from astropy import units as u
from astropy.modeling.models import Scale

import gwcs.coordinate_frames as cf
from . import pointing
from .util import not_implemented_mode, subarray_transform


def create_pipeline(input_model, reference_files):
    '''
    get reference files from crds

    '''
    exp_type = input_model.meta.exposure.type.lower()
    pipeline = exp_type2transform[exp_type](input_model, reference_files)

    return pipeline


def imaging(input_model, reference_files):
    """
    The NIRCAM imaging pipeline includes 3 coordinate frames -
    detector, focal plane and sky

    reference_files={'distortion': 'test.asdf', 'filter_offsets': 'filter_offsets.asdf'}
    """
    detector = cf.Frame2D(name='detector', axes_order=(0, 1), unit=(u.pix, u.pix))
    v2v3 = cf.Frame2D(name='v2v3', axes_order=(0, 1), unit=(u.deg, u.deg))
    world = cf.CelestialFrame(reference_frame=coord.ICRS(), name='world')

    subarray2full = subarray_transform(input_model)
    imdistortion = imaging_distortion(input_model, reference_files)
    distortion = subarray2full | imdistortion
    distortion.bounding_box = imdistortion.bounding_box
    del imdistortion.bounding_box
    tel2sky = pointing.v23tosky(input_model)
    pipeline = [(detector, distortion),
                (v2v3, tel2sky),
                (world, None)]
    return pipeline


def imaging_distortion(input_model, reference_files):
    distortion = AsdfFile.open(reference_files['distortion']).tree['model']
    # Convert to deg - output of distortion models is in arcsec.
    transform = distortion | Scale(1 / 3600) & Scale(1 / 3600)

    try:
        bb = transform.bounding_box
    except NotImplementedError:
        shape = input_model.data.shape
        # Note: Since bounding_box is attached to the model here it's in reverse order.
        transform.bounding_box = ((-0.5, shape[0] - 0.5),
                                  (-0.5, shape[1] - 0.5))
    return transform


exp_type2transform = {'nrc_image': imaging,
                      'nrc_grism': not_implemented_mode,
                      'nrc_tacq': imaging,
                      'nrc_taconfirm': imaging,
                      'nrc_coron': not_implemented_mode,
                      'nrc_focus': imaging,
                      'nrc_tsimage': imaging,
                      'nrc_tsgrism': not_implemented_mode,
                      'nrc_led': not_implemented_mode,
                      'nrc_dark': not_implemented_mode,
                      'nrc_flat': not_implemented_mode,
                      }
