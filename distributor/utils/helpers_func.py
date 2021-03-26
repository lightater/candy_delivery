from distributor.db.schema import TransportType
import datetime


def calc_courier_carrying(courier_type):
    if courier_type == TransportType.foot:
        return 10
    elif courier_type == TransportType.bike:
        return 15
    elif courier_type == TransportType.car:
        return 50
    else:
        raise ValueError('courier_type not present in TransportType')


def time_in_range(start, end, x):
    return start <= x <= end if start <= end else start <= x or x <= end


def str_to_time(str_data):
    try:
        time_obj = datetime.datetime.strptime(str_data, '%H:%M')
    except ValueError:
        print(f'{str_data} is not in format %H:%M')
        raise
    return time_obj


def overlap(first_arr, second_arr):
    for f_time in first_arr:
        for s_time in second_arr:
            start1, end1 = str_to_time(f_time[:5]), str_to_time(f_time[6:])
            start2, end2 = str_to_time(s_time[:5]), str_to_time(s_time[6:])
            if time_in_range(start1, end1, start2) or \
                    time_in_range(start2, end2, start1):
                return True
    return False
