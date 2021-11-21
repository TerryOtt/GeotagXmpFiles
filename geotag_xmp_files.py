import gpxpy
import argparse
import glob
import os
import pprint
import xml.etree.ElementTree
import datetime
import json


def _parse_args():
    arg_parser = argparse.ArgumentParser(description="Add geotags to XMP sidecar files")
    arg_parser.add_argument( "xmp_dir", help="Directory with XMP files")
    arg_parser.add_argument( "gpx_dir", help="Directory with GPX files")

    return arg_parser.parse_args()


def _read_gpx_files(args):
    # Find all GPX files in the specified dir
    gpx_files = glob.glob( os.path.join( args.gpx_dir, "*.gpx") )
    #pprint.pprint( gpx_files )
    gpxpy_handles = []
    print( "Reading GPX files")
    for curr_gpx_file in gpx_files:
        with open( curr_gpx_file, 'r' ) as gpx_handle:
            gpx_data = gpxpy.parse(gpx_handle)
            gpxpy_handles.append( gpx_data)
            print( f"\tRead {curr_gpx_file}")

    return gpxpy_handles


def _geotag_xmp_files( args, gpx_files ):
    print( "\nGeotagging XMP files")
    xmp_file_list = glob.glob( os.path.join( args.xmp_dir, "*.xmp"))

    feet_in_one_meter = 3.28084

    for curr_xmp_filename in xmp_file_list:
        curr_xml_tree = xml.etree.ElementTree.parse(curr_xmp_filename )
        print( f"\tParsed {curr_xmp_filename}")
        root_node = curr_xml_tree.getroot()

        # Find date/time
        namespaces = {'exif': 'http://ns.adobe.com/exif/1.0/'}
        found_datetime_node = root_node.find( ".//exif:DateTimeOriginal", namespaces)
        if found_datetime_node is None:
            raise ValueError("Found XMP file with no exif:DateTimeOriginal tag")
        xmp_datetime = datetime.datetime.fromisoformat( found_datetime_node.text)

        # Make the datetime timezone aware
        xmp_datetime = xmp_datetime.replace(tzinfo=datetime.timezone.utc)
        print( f"\t\tDateTime: {xmp_datetime.isoformat()}")

        # Find lat/lon/alt based on date/time
        for curr_gpx_data in gpx_files:
            computed_location = curr_gpx_data.get_location_at( xmp_datetime )
            if computed_location:
                print( "Found computed location" )
                break

        if computed_location:
            location_info = {
                'latitude_wgs84_degrees': computed_location[0].latitude,
                'longitude_wgs84_degrees': computed_location[0].longitude,
                'elevation_above_sea_level': {
                    'meters': computed_location[0].elevation,
                    'feet': computed_location[0].elevation * feet_in_one_meter,
                },
            }
        else:
            raise ValueError("\t\tCould not geotag file")

        print(f"\t\tComputed location info:\n{json.dumps(location_info, indent=4, sort_keys=True)}")

        # Update XML with lat/lon/alt

        # Save XML out

        break

def _main():
    args = _parse_args()
    gpx_files = _read_gpx_files(args)
    #pprint.pprint( gpx_files )
    _geotag_xmp_files( args, gpx_files )

if __name__ == "__main__":
    _main()