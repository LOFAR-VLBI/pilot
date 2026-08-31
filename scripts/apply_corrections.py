import numpy as np
from astropy.io import fits
from astropy.table import Table
import os
import glob
from astropy import units as u

path='/cosma8/data/do011/dc-esco1/postprocessing/restored_post/correct_compact/'

medians = Table.read('overall_medians.csv', format="csv")
ra_per_facets = glob.glob(os.path.join(path+'/ra_offset_source_catalogue_facet_*'))
dec_per_facets = glob.glob(os.path.join(path+'/dec_offset_source_catalogue_facet_*'))

#print(medians, ra_per_facets)


facet_medians = Table.read(path+'/facets_average.csv', format="csv")

scale = medians['median_overall_scale'].data
#ra_offset = medians['median_overall_ra'].data
#dec_offset = medians['median_overall_dec'].data

fitfacets = glob.glob(os.path.join(path+'/subtracted_restored_0.3/*_posra.fits')) ##where im getting the ra and dec from which can be negative but needs to be positive, also must be restored beam

#print(fitfacets)
for ra_per_facet in ra_per_facets:
     prefixoldra = ra_per_facet.split('/')[-1].replace('fits','')
     prefixra = prefixoldra.replace('ra_offset_','')
     ra_facet = ra_per_facet.split('/')[-1].split('_')[5].split('-')[0]
     #print(ra_facet)
     for dec_per_facet in dec_per_facets:
         prefixolddec = dec_per_facet.split('/')[-1].replace('fits','')
         prefixdec = prefixolddec.replace('dec_offset_','')
         dec_facet = dec_per_facet.split('/')[-1].split('_')[5].split('-')[0]
         for fitfacet in fitfacets:
             prefix = fitfacet.split('/')[-1].replace('.fits','')
             facet = fitfacet.split('/')[-1].split('_')[1].split('-')[0]
             #print(facet)
             if facet==ra_facet and facet==dec_facet:
                print(facet, ra_facet, dec_facet)

                with fits.open(fitfacet) as hdu:
                     ra_im = hdu[0].header['CRVAL1']
                     dec_im = hdu[0].header['CRVAL2']
                     if ra_facet!='00':
                        median_fa = facet_medians[np.where((facet_medians['ra_facets'].data==float(ra_facet.strip('0'))))[0][0]]
                     if ra_facet == '00':
                        median_fa = facet_medians[np.where((facet_medians['ra_facets'].data==float(0)))[0][0]]
                     #print(type(facet_medians['ra_facets'].data), type(float(ra_facet.strip('0'))))
                     #print(np.where((facet_medians['ra_facets'].data==float(ra_facet.strip('0'))))[0][0])
                     ra_median_arc = median_fa['median_ra_offset']*u.arcsec
                     dec_median_arc = median_fa['median_dec_offset']*u.arcsec
                     ra_median = ra_median_arc.to(u.deg)
                     dec_median = dec_median_arc.to(u.deg)
                     #print(ra_median, dec_median)
                     #if ra_median>=0:
                     ra_new = ra_im+ra_median.value
                     #if dec_median>=0:
                     dec_new = dec_im+dec_median.value
                     hdr = hdu[0].header
                     hdu[0].header['CRVAL1']=float(ra_new)
                     hdu[0].header['CRVAL2']=float(dec_new)
                     print(ra_im, float(ra_new), hdu[0].header['CRVAL1'])
                     print(dec_im, float(dec_new), hdu[0].header['CRVAL2'])
                     hdu.writeto(prefix+'updatedastro_03.fits',overwrite=True) ##only has astrometry corrected
                
                with fits.open(prefix+'updatedastro_03.fits') as hdu2:
                     flux = hdu2[0].data
                     new_flux = flux/scale
                     #print(flux[2], new_flux[2])
                     hdu2[0].data = new_flux
                     #print(hdu2[0].data[2],new_flux[2])
                     hdu2.writeto(prefix+'updatedastroandflux_03.fits',overwrite=True) ##both astronometry and flux scaling




'''


for facet in facets:
    prefix = facet.split('/')[-1].replace('.fits','')
    print(prefix)
    with fits.open(facet) as hdu: ##### make this pb
         ra_im = hdu[0].header['CRVAL1']
         dec_im = hdu[0].header['CRVAL2']
         median_ra = medians['median_overall_ra']
         median_dec = medians['median_overall_dec']
         median_scale = medians['median_overall_scale']
         if median_ra>=0:
            ra_new = ra_im-ra_offset
         if median_dec>=0:
            dec_new = dec_im-median_dec
         hdr = hdu[0].header
         hdu[0].header['CRVAL1']=float(ra_new)
         hdu[0].header['CRVAL2']=float(dec_new)
#         print(hdu[0].header['CRVAL1'], float(ra_new))
         hdu.writeto(prefix+'updatedastro.fits',overwrite=True)

    with fits.open(prefix+'updatedastro.fits') as hdu2:
         flux = hdu2[0].data
         new_flux = flux/median_scale
         print(flux[2], new_flux[2])
         hdu2[0].data = new_flux

         print(hdu2[0].data[2],new_flux[2])
         hdu2.writeto(prefix+'updatedastroandflux.fits',overwrite=True)

os.system('mkdir corrected_facets')
os.system('mv *updatedastroandflux.fits corrected_facets/.')
os.system('/cosma8/data/do011/dc-esco1/subarc_scratch/0.3_image/swarp/src/swarp -c mosiac.cfg corrected_facets/*')

'''
