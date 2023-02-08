import os, sys
import pandas as pd
import numpy as np
import geopandas as gpd
from dotenv import load_dotenv
from pathlib import Path
from math import isnan
import shapely.speedups
import datetime
import swifter
import click
shapely.speedups.enable()

'''
The purpose of this script is to highlight potentially problematic building footprints as they relate to associated parcel fabrics and building points.
Generates a report of counts based on known potentially problematic situations

Examples of potentially problematic situations include (examples with ✓ are those that have been added rest are planned):

Footprints:
- Footprint intersects with multiple parcels ✓
- Footprint contains many points with many unique addresses
- Footprint not within a parcel ✓
- Multiple footprints within one parcel

Points:
- Point not within parcel ✓
- Multipoint within one parcel ✓
- More points than buildings in a parcel ✓

'''

# -------------------------------------------------------
# Class

class IssueFlagging:
    '''
    The purpose of this class is to highlight the relationships between a parcels layer and a address point layer
    '''
    def __init__(self, ap_data: gpd.GeoDataFrame, bp_data:gpd.GeoDataFrame, crs= 4326):
       
        # Core data import
        self.addresses = ap_data
        self.footprints = bp_data    
    
    def __call__():

        self.footprints.to_crs(crs=proj_crs, inplace=True)
        self.addresses.to_crs(crs=proj_crs, inplace=True)

        # produce basic layers
        print('Grouping APs')
        grouped_ap = self.addresses.groupby('link_field', dropna=True)['link_field'].count()
        print('Grouping BFs')
        grouped_bf = self.footprints[self.footprints['shed_flag'] == False].groupby('link_field', dropna=True)['link_field'].count()
        print('Determining Relationships')
        self.addresses['parcel_rel'] = self.addresses['link_field'].apply(lambda x: self.relationship_setter(x, grouped_ap, grouped_bf))


    def relationship_setter(self, parcel_ident, ap_parcel_counts, bf_parcel_counts):
            '''Returns the parcel relationship type for the given record based on the counts of the parcel linkages in the bf and ap datasets'''
            from math import isnan
            if isnan(parcel_ident):
                return 'unlinked'
            bf_indexes = bf_parcel_counts.index.tolist()

            if not parcel_ident in bf_indexes:
                return 'no_linked_building'

            ap_count = ap_parcel_counts[ap_parcel_counts.index == parcel_ident].tolist()[0]
            bf_count = bf_parcel_counts[bf_parcel_counts.index == parcel_ident].tolist()[0]

            if (ap_count == 1) and (bf_count == 1):
                return 'one_to_one'

            if (ap_count == 1) and (bf_count > 1):
                return 'one_to_many'

            if (ap_count > 1) and (bf_count == 1):
                return 'many_to_one'

            if (ap_count > 1) and (bf_count > 1):
                return 'many_to_many'

            print(ap_count)
            print(bf_count)
            sys.exit()


    def export_results(self, out_path:str, out_lyr_name='ap_full'):
        '''outputs results to '''
        self.addresses.to_file(out_path, layer=out_lyr_name)
   

def main():

    load_dotenv(os.path.join(r'C:\projects\point_in_polygon\scripts', 'NB_environments.env'))
    bf_path =  Path(os.getenv('DATA_GPKG'))
    bf_lyr_nme = 'footprints_cleaned'
    # bf_lyr_nme = 'footprint_linkages'
    
    ap_path = Path(os.getenv('DATA_GPKG'))
    ap_lyr_nme = 'addresses_cleaned'
    # ap_path = Path(os.getenv('ADDRESS_PATH'))
    # ap_lyr_nme = os.getenv('ADDRESS_LAYER')

    linking_data_path = Path(os.getenv('DATA_GPKG'))
    linking_lyr_nme = 'parcels_cleaned'

    output_gpkg = Path(os.getenv('DATA_GPKG'))

    proj_crs = int(os.getenv('PROJ_CRS'))

    aoi_mask = os.getenv('AOI_MASK')

    metrics_out_path = Path(os.getenv('METRICS_CSV_OUT_PATH'))

    ap_cases_gpkg = Path(os.getenv('AP_CASES_GPKG'))

    issues_flagged = IssueFlagging(ap_path, bf_path, linking_data_path, ap_lyr_nme, bf_lyr_nme, linking_lyr_nme, aoi_mask,crs=proj_crs)
    issues_flagged.export_results(output_gpkg, out_lyr_name='ap_full')
    
    
if __name__ == "__main__":
    main()
    print('DONE!')

