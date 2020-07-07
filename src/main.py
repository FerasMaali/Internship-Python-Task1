#!/usr/bin/env python3

import datetime
import logging
import yaml
import json
import argparse
import tarfile
import os
import shutil

def main():
    init_logger()

    global args
    args = get_arguments()

    # create destination directory
    os.mkdir(args.output_directory, mode=0o744)

    # move rpm files to destination directory
    rpm_list = move_rpms()

    # read the manifest from the yaml file
    manifest = load_yaml(args.input_file)

    # write manifest to a json file
    write_manifest(manifest)

    # extract release notes and write them to their file
    write_release_notes(manifest, rpm_list)

    # compress the folder to produce the result
    compress_folder(args.output_file, args.output_directory)

    if args.clean:
        shutil.rmtree(args.output_directory)
        logging.debug('remove output directory')


def move_rpms():
    rpm_list = os.listdir(args.rpms_directory)

    for xfile in rpm_list:
        src = os.path.join(args.rpms_directory, xfile)
        dest = os.path.join(args.output_directory, xfile)
        shutil.copyfile(src, dest)

    logging.debug('moved rpms to output directory')

    return rpm_list


def compress_folder(output_file, output_directory):
    with tarfile.open(output_file, "w:gz") as tar:
        tar.add(output_directory, arcname=os.path.sep)
    logging.debug('finished compressing {0}'.format(args.output_file))


def write_release_notes(data, rpm_list):
    with open(os.path.join(args.output_directory, args.release_notes_file), 'w') as output_file:
        # Writing patch fixes to the file
        output_file.write('The CVM_PE_GI-7.7r1.7.1-'
                          + f'{datetime.datetime.now():%Y%m%d}'
                          + ' patch fixes the following CVEs:\n')
        for fix in get_patch_fixes(data):
            output_file.write('  ' + fix + '\n')

        # Writing rpms list to the release_notes file
        output_file.write('\nNew patches included in this bundle:\n')
        for rpm in rpm_list:
            output_file.write('  ' + rpm + '\n')

        # Writing targeted releases
        output_file.write('\nTargeted releases:\n')
        for release in get_targeted_releases(data):
            output_file.write('  ' + release + '\n')

    logging.debug('release_notes file was written successfully')


def get_patch_fixes(data):
    return [x['CESA'] for x in data['CESA_list']]


def get_targeted_releases(data):
    return ['7.7r1.7', '7.7r1.6', '7.7r1.5.1', '7.6r2']


def write_manifest(data):
    with open(os.path.join(args.output_directory, args.manifest_file), 'w') as output_file:
        json.dump(data, output_file, indent=2)
    logging.debug('Manifest file was written successfully')


def init_logger():
    logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(name)s.%(funcName)-15s +%(lineno)s: %(levelname)-8s %(message)s'
        )
    logging.debug('logging started working')


def get_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--input-file',
        help='Input YAML file',
        required=True
    )

    parser.add_argument(
        '--rpms-directory',
        help='Directory containing RPM files',
        required=True
    )

    parser.add_argument(
        '--output-file',
        help='Output file name',
        default='CVM_PE_GI-7.7r1.6.1-' + f'{datetime.datetime.now():%Y%m%d}' + '-x86_64.tar.gz'
    )

    parser.add_argument(
        '--output-directory',
        help='Output directory name',
        default='CVM_PE_GI-7.7r1.6.1-' + f'{datetime.datetime.now():%Y%m%d}' + '-x86_64'
    )

    parser.add_argument(
        '--release-notes-file',
        help='release notes file name',
        default='CVM_PE_GI-7.7r1.7.1-' + f'{datetime.datetime.now():%Y%m%d}' + '-x86_64.release_notes'
    )

    parser.add_argument(
        '--manifest-file',
        help='manifest file name',
        default='CVM_RPM_LIST_MANIFEST.json'
    )

    parser.add_argument(
        '--clean',
        help='whether to clean output directory of not',
        action='store_true'
    )

    args = parser.parse_args()

    logging.debug('args were successfully collected')
    logging.debug('args = ' + str( args ))

    return args


def load_yaml(file_name):
    if type(file_name) is not str:
        raise TypeError('file_name must be a string')

    with open(file_name, 'r') as stream:
        try:
            result = yaml.safe_load(stream)
            logging.debug('done reading {0}'.format(args.input_file))
            return result
        except yaml.YAMLError as exc:
            print(exc)


if __name__ == '__main__':
    main()
