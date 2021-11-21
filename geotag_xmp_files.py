import gpxpy
import argparse
import glob
import os
import pprint
import xml.etree.ElementTree

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

    for curr_xmp_filename in xmp_file_list:
        curr_xml_tree = xml.etree.ElementTree.parse(curr_xmp_filename )
        print( f"\tParsed {curr_xmp_filename}")
        break

def _main():
    args = _parse_args()
    gpx_files = _read_gpx_files(args)
    #pprint.pprint( gpx_files )
    _geotag_xmp_files( args, gpx_files )

if __name__ == "__main__":
    _main()