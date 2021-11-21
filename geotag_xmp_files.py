import argparse
import glob
import os.path
import pprint
import exiftool
import shutil
import multiprocessing
import queue


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

    max_queue_size = len(image_file_list)

    file_geotagging_queue = multiprocessing.Queue(max_queue_size)
    all_files_written_to_queue = multiprocessing.Event()

    # Create a worker process for each CPU on the host
    process_handles = []
    for i in range( multiprocessing.cpu_count() ):
        curr_process_handle = multiprocessing.Process( target=_geotag_worker,
                                                       args=( i+1, args, file_geotagging_queue, all_files_written_to_queue ) )
        curr_process_handle.start()
        process_handles.append( curr_process_handle )

    for curr_image_file in sorted(image_file_list):
        file_geotagging_queue.put( curr_image_file )

    # Note that all files have been written to queue, children can come home now
    all_files_written_to_queue.set()

    # Wait for all children to rejoin
    while process_handles:
        curr_join_handle = process_handles.pop()
        curr_join_handle.join()

    print( "All worker processes have rejoined" )


def _geotag_worker( worker_num, args, file_geotagging_queue, all_files_written_to_queue ):
    queue_read_timeout_seconds = 0.1
    gpx_wildcard = os.path.join(args.gpx_dir, "*.gpx")

    with exiftool.ExifTool() as exiftool_handle:

        while True:
            try:
                curr_image_file = file_geotagging_queue.get( timeout=queue_read_timeout_seconds )

            except queue.Empty:
                if all_files_written_to_queue.is_set():
                    break
                else:
                    continue

            (basename_minus_ext, file_extension) = os.path.splitext(os.path.basename( curr_image_file))

            # Create base XMP
            exiftool_params = (
                #"-v2".encode(),
                exiftool.fsencode(curr_image_file),
                "-o".encode(),
                "%d%f.xmp".encode(),
            )
            execute_output = exiftool_handle.execute( *exiftool_params )
            #print( f"\t\tCreated base XMP {basename_minus_ext}.xmp")
            #print( f"Output:{execute_output.decode()}")

            # Geotag XMP
            exiftool_params = (
                #"-v2".encode(),
                "-geotag".encode(),
                gpx_wildcard.encode(),
                "-geotime<${DateTimeOriginal}+00:00".encode(),
                exiftool.fsencode( os.path.join( args.image_dir, f"{basename_minus_ext}.xmp") ),
                "-o".encode(),
                "%d%f_geocode.xmp".encode(),
            )

            #print( exiftool_params )

            execute_output = exiftool_handle.execute(*exiftool_params)
            #print(f"\t\tGeotagged into {basename_minus_ext}_geocode.xmp\n")
            #print( f"Output:{execute_output.decode()}")

            # Overwrite base XMP with the geotagged version
            final_xmp_path = os.path.join( args.image_dir, f"{basename_minus_ext}.xmp" )
            geocoded_xmp_path = os.path.join( args.image_dir, f"{basename_minus_ext}_geocode.xmp")
            shutil.move( geocoded_xmp_path, final_xmp_path )

            print( f"Worker {worker_num} created geotagged XMP for {curr_image_file}" )

    print( f"Worker {worker_num} exiting cleanly" )


def _main():
    args = _parse_args()
    #pprint.pprint( args )
    _geotag_xmp_files( args )


if __name__ == "__main__":
    _main()