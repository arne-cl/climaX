#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <climax.programming@arne.cl>

"""
This script reads the parameters culture_id, flowering date, soil volume and
field capacity from a tab-separated file and writes climate data to a
tab-separated file (drought before flowering, drought after flowering,
cold-before, cold-after, heat-before, heat-after, light-before, light-after).
"""

import sys
import argparse
import traceback

from climate_data import get_climate_data
import login


def get_climate_data_from_str(cursor, parameter_line):
    """
    Parameters
    ----------
    cursor : MySQLdb.cursors.Cursor
        a cursor to the (running) database
    parameter_line : str
        one line from a tab-separated file containing culture_id,
        flowering date, soil volume and field capacity

    Returns
    -------
    culture_id, temp_stress_days, drought_stress_days, light_intensity
    """
    global CURSOR
    CURSOR = cursor
    global CONNECTED_TO_DB
    CONNECTED_TO_DB = False

    columns = parameter_line.split('\t')
    assert len(columns) == 4, "Line {0} in file {1} doesn't contain 4 columns"
    culture_id, date, soil_volume, field_capacity = parameter_line.split('\t')
    return int(culture_id), get_climate_data(int(culture_id), date,
                                             float(soil_volume),
                                             float(field_capacity))


def format_climate_data(climate_data):
    """
    formats climate data (climate_id, irrigation, temp_stress_days, drought_stress_days,
    light_intensity) for tab-separated output.
    """
    culture_id, (irrigation, temp_stress_days, drought_stress_days, light_intensity) = climate_data
    climate_str = (
        '{culture_id}\t{drought_before}\t{drought_after}\t{control_drought_before}'
        '\t{control_drought_after}\t{stress_drought_before}\t{stress_drought_after}'
         '\t{cold_before}\t{cold_after}\t{heat_before}\t{heat_after}'
         '\t{light_before}\t{light_after}\n')

    # WARNING: WORKAROUND for clusterfuck in database management, cf. issue #6
    if irrigation and culture_id not in (47109, 56879):
        control_dsds, stress_dsds = drought_stress_days
        return climate_str.format(
            culture_id=culture_id,
            drought_before='NA', drought_after='NA',
            control_drought_before=control_dsds[0],
            control_drought_after=control_dsds[1],
            stress_drought_before=stress_dsds[0],
            stress_drought_after=stress_dsds[1],
            cold_before=temp_stress_days[0], cold_after=temp_stress_days[1],
            heat_before=temp_stress_days[2], heat_after=temp_stress_days[3],
            light_before=light_intensity[0], light_after=light_intensity[1])
    else:
        return climate_str.format(
            culture_id=culture_id,
            drought_before=drought_stress_days[0],
            drought_after=drought_stress_days[1],
            control_drought_before='NA', control_drought_after='NA',
            stress_drought_before='NA', stress_drought_after='NA',
            cold_before=temp_stress_days[0], cold_after=temp_stress_days[1],
            heat_before=temp_stress_days[2], heat_after=temp_stress_days[3],
            light_before=light_intensity[0], light_after=light_intensity[1])


def main(args=None):
    """calls get_climate_data with arguments from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_file', type=argparse.FileType('r'),
        help=("tsv-file containing culture_id, flowering date, soil volume "
              "and field capacity"))
    parser.add_argument(
        'output_file', nargs='?', default=sys.stdout,
        type=argparse.FileType('w'),
        help=("tsv-file containing drought stress days (DSDs) (before/after "
              "flowering) OR control DSDs (before/after) and stress DSD "
              "(before/after), cold stress days (before/after flowering), "
              "heat stress days (before/after flowering) and light sum "
              "(before/after flowering). writes to STDOUT, if no filename "
              "is given."))
    args = parser.parse_args(sys.argv[1:])

    if not args.input_file:
        sys.exit(1)

    database = login.get_db()
    cursor = database.cursor()

    args.output_file.write(
        ('culture-id\tdrought-before\tdrought-after\tcontrol-drought-before'
         '\tcontrol-drought-after\tstress-drought-before\tstress-drought-after'
         '\tcold-before\tcold-after\theat-before\theat-after'
         '\tlight-before\tlight-after\n'))

    for i, line in enumerate(args.input_file, 1):
        try:
            climate_data = get_climate_data_from_str(cursor, line)
            args.output_file.write(format_climate_data(climate_data))
        except Exception as e:
            sys.stderr.write('line {} in file {} caused trouble: {}'.format(i, args.input_file.name, line))
            sys.stderr.write(traceback.format_exc())


if __name__ == '__main__':
    main(sys.argv[1:])
