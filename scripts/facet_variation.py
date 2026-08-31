from astropy.table import Table,vstack
import numpy as np
import os
import glob
import csv

path='/cosma8/data/do011/dc-esco1/postprocessing/restored_post/correct_compact/'

files = glob.glob(os.path.join(path+'/flux_scale_source_matches_source_catalogue_facet*')) ##flux_scale_source_matches_source_catalouge_facet previous
ra_offsets = glob.glob(os.path.join(path+'/ra_offset_source_catalogue_facet_*'))
dec_offsets = glob.glob(os.path.join(path+'/dec_offset_source_catalogue_facet_*'))

## I AM MANUALLY GOING TO MAKE FLUX_SCAL* FOR EMPTY FACTS 00,11,14,25 SO THE LOOP WORKS
medians = []
facets = []
facets_ras = []
facets_decs = []
ra_offs = []
dec_offs = []

all_scales = []
all_ra = []
all_dec = []

all_scales=Table()
all_dec = Table()
all_ra = Table()

for file in files:
	facet = file.split('/')[-1].split('_')[7].split('-')[0]
	for ra_offset in ra_offsets:
		facets_ra = ra_offset.split('/')[-1].split('_')[5].split('-')[0]
		for dec_offset in dec_offsets:
			facets_dec = dec_offset.split('/')[-1].split('_')[5].split('-')[0]
			if facet==facets_ra and facet==facets_dec:
				facets.append(file.split('/')[-1].split('_')[7].split('-')[0])
				facets_ras.append(ra_offset.split('/')[-1].split('_')[5].split('-')[0])
				facets_decs.append(dec_offset.split('/')[-1].split('_')[5].split('-')[0]) 
				table_flux = Table.read(file, format="csv")
				print(len(table_flux))
				scale = table_flux['flux_scale']
				all_scales = vstack([all_scales,scale])
				median = np.median(scale)
				medians.append(median)
				table_ra = Table.read(ra_offset, format="csv")
				ra = table_ra['ra_offset']
				all_ra = vstack([all_ra,ra])
				median_off = np.median(ra)
				ra_offs.append(median_off)

				table_dec = Table.read(dec_offset, format="csv")
				dec = table_dec['dec_offset']
				all_dec = vstack([all_dec,dec])
				median_off_dec = np.median(dec)
				dec_offs.append(median_off_dec)


T = Table()
T['facet'] = facets
T['ra_facets'] = facets_ras
T['dec_facets'] = facets_decs
T['median_flux_scale'] = medians
T['median_ra_offset'] = ra_offs
T['median_dec_offset'] = dec_offs

T.write('facets_average.csv', format="csv", overwrite=True)

Y = Table()
Y['ra_offset'] = all_ra
Y['dec_offset'] = all_dec

Y.write('all_info_astro.csv',format="csv", overwrite=True)

Z=Table()
Z['flux_scaling'] = all_scales
Z.write('all_info_flux.csv',format="csv", overwrite=True)


overall_median_scale = np.median(all_scales['flux_scale'])
overall_median_ra = np.median(all_ra['ra_offset'])
overall_median_dec = np.median(all_dec['dec_offset'])

print(overall_median_dec)

data = [['median_overall_scale', 'median_overall_ra', 'median_overall_dec'], #headers
	[overall_median_scale, overall_median_ra, overall_median_dec ]]

with open("overall_medians.csv", mode="w", newline="") as file:
	writer=csv.writer(file)
	writer.writerows(data)
