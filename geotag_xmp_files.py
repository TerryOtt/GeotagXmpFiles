import argparse
import glob
import os
import pprint
import exiftool


def _parse_args():
    arg_parser = argparse.ArgumentParser(description="Add geotags to XMP sidecar files")
    arg_parser.add_argument( "image_dir", help="Directory with image files")
    arg_parser.add_argument( "image_file_ext", help="File extension for image files")
    arg_parser.add_argument( "gpx_dir", help="Directory with GPX files")

    return arg_parser.parse_args()


def _get_image_file_list(args):
    return glob.glob( os.path.join( args.image_dir, f"*.{args.image_file_ext}"))

def _geotag_xmp_files( args ):
    print( f"Geotagging image files with extension \".{args.image_file_ext}\" in {args.image_dir}" )
    image_file_list = _get_image_file_list( args )
    #pprint.pprint( image_file_list )
    gpx_wildcard = os.path.join( args.gpx_dir, "*.gpx")

    with exiftool.ExifTool() as exiftool_handle:

        for curr_image_file in image_file_list:
            print( f"\tGeotagging {curr_image_file}" )

            (basename_minus_ext, file_extension) = os.path.splitext(os.path.basename( curr_image_file))

            # Create base XMP
            exiftool_params = (
                #"-v2".encode(),
                exiftool.fsencode(curr_image_file),
                "-o".encode(),
                "%d%f.xmp".encode(),
            )
            execute_output = exiftool_handle.execute( *exiftool_params )
            print( f"\t\tCreated base XMP {basename_minus_ext}.xmp\n")
            #print( f"Output:{execute_output.decode()}")

            # Geotag XMP
            exiftool_params = (
                "-v2".encode(),
                "-geotag".encode(),
                gpx_wildcard.encode(),
                "-geotime<${DateTimeOriginal}+00:00".encode(),
                exiftool.fsencode( os.path.join( args.image_dir, f"{basename_minus_ext}.xmp") ),
                "-o".encode(),
                "%d%f_geocode.xmp".encode(),
            )

            print( exiftool_params )

            execute_output = exiftool_handle.execute(*exiftool_params)
            print(f"\t\tGeotagged into {basename_minus_ext}_geocode.xmp\n")
            print( f"Output:{execute_output.decode()}")

            break

def _main():
    args = _parse_args()
    pprint.pprint( args )
    _geotag_xmp_files( args )


if __name__ == "__main__":
    _main()