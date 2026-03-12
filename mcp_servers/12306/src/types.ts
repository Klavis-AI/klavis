#!/usr/bin/env node
export type TicketData = {
    secret_Sstr: string;
    button_text_info: string;
    train_no: string;
    station_train_code: string;
    start_station_telecode: string;
    end_station_telecode: string;
    from_station_telecode: string;
    to_station_telecode: string;
    start_time: string;
    arrive_time: string;
    lishi: string;
    canWebBuy: string;
    yp_info: string;
    start_train_date: string;
    train_seat_feature: string;
    location_code: string;
    from_station_no: string;
    to_station_no: string;
    is_support_card: string;
    controlled_train_flag: string;
    gg_num: string;
    gr_num: string;
    qt_num: string;
    rw_num: string;
    rz_num: string;
    tz_num: string;
    wz_num: string;
    yb_num: string;
    yw_num: string;
    yz_num: string;
    ze_num: string;
    zy_num: string;
    swz_num: string;
    srrb_num: string;
    yp_ex: string;
    seat_types: string;
    exchange_train_flag: string;
    houbu_train_flag: string;
    houbu_seat_limit: string;
    yp_info_new: string;
    '40': string;
    '41': string;
    '42': string;
    '43': string;
    '44': string;
    '45': string;
    dw_flag: string;
    '47': string;
    stopcheckTime: string;
    country_flag: string;
    local_arrive_time: string;
    local_start_time: string;
    '52': string;
    bed_level_info: string;
    seat_discount_info: string;
    sale_time: string;
    '56': string;
};

export const TicketDataKeys: (keyof TicketData)[] = [
    'secret_Sstr',
    'button_text_info',
    'train_no',
    'station_train_code',
    'start_station_telecode',
    'end_station_telecode',
    'from_station_telecode',
    'to_station_telecode',
    'start_time',
    'arrive_time',
    'lishi',
    'canWebBuy',
    'yp_info',
    'start_train_date',
    'train_seat_feature',
    'location_code',
    'from_station_no',
    'to_station_no',
    'is_support_card',
    'controlled_train_flag',
    'gg_num',
    'gr_num',
    'qt_num',
    'rw_num',
    'rz_num',
    'tz_num',
    'wz_num',
    'yb_num',
    'yw_num',
    'yz_num',
    'ze_num',
    'zy_num',
    'swz_num',
    'srrb_num',
    'yp_ex',
    'seat_types',
    'exchange_train_flag',
    'houbu_train_flag',
    'houbu_seat_limit',
    'yp_info_new',
    '40',
    '41',
    '42',
    '43',
    '44',
    '45',
    'dw_flag',
    '47',
    'stopcheckTime',
    'country_flag',
    'local_arrive_time',
    'local_start_time',
    '52',
    'bed_level_info',
    'seat_discount_info',
    'sale_time',
    '56',
];

export type TicketInfo = {
    train_no: string;
    start_train_code: string;
    start_date: string;
    start_time: string;
    arrive_date: string;
    arrive_time: string;
    lishi: string;
    from_station: string;
    to_station: string;
    from_station_telecode: string;
    to_station_telecode: string;
    prices: Price[];
    dw_flag: string[];
};

export type StationData = {
    station_id: string;
    station_name: string;
    station_code: string;
    station_pinyin: string;
    station_short: string;
    station_index: string;
    code: string;
    city: string;
    r1: string;
    r2: string;
};

export const StationDataKeys: (keyof StationData)[] = [
    'station_id',
    'station_name',
    'station_code',
    'station_pinyin',
    'station_short',
    'station_index',
    'code',
    'city',
    'r1',
    'r2',
];

export interface Price {
    seat_name: string;
    short: string;
    seat_type_code: string;
    num: string;
    price: number;
    discount: number | null;
}

export type RouteStationData = {
    arrive_time: string;
    station_name: string;
    isChina: string;
    start_time: string;
    stopover_time: string;
    station_no: string;
    country_code: string;
    country_name: string;
    isEnabled: boolean;
    train_class_name?: string;
    service_type?: string;
    end_station_name?: string;
    start_station_name?: string;
    station_train_code?: string;
};

export type RouteStationInfo = {
    arrive_time: string;
    station_name: string;
    stopover_time: string;
    station_no: number;
};

export type InterlineData = {
    all_lishi: string;
    all_lishi_minutes: number;
    arrive_date: string;
    arrive_time: string;
    end_station_code: string;
    end_station_name: string;
    first_train_no: string;
    from_station_code: string;
    from_station_name: string;
    fullList: InterlineTicketData[];
    isHeatTrain: string;
    isOutStation: string;
    lCWaitTime: string;
    lishi_flag: string;
    middle_date: string;
    middle_station_code: string;
    middle_station_name: string;
    same_station: string;
    same_train: string;
    score: number;
    score_str: string;
    scretstr: string;
    second_train_no: string;
    start_time: string;
    train_count: number;
    train_date: string; // 出发时间
    use_time: string;
    wait_time: string;
    wait_time_minutes: number;
};

export type InterlineInfo = {
    lishi: string;
    //all_lishi_minutes: number;
    start_time: string;
    start_date: string;
    middle_date: string;
    arrive_date: string;
    arrive_time: string;
    from_station_code: string;
    from_station_name: string;
    middle_station_code: string;
    middle_station_name: string;
    end_station_code: string;
    end_station_name: string;
    start_train_code: string; // 用于过滤
    first_train_no: string;
    second_train_no: string;
    train_count: number;
    ticketList: TicketInfo[];
    //isHeatTrain: string;
    //isOutStation: string;
    //lCWaitTime: string;
    //lishi_flag: string;
    same_station: boolean;
    same_train: boolean;
    wait_time: string;
    //wait_time_minutes: number;
};

export type InterlineTicketData = {
    arrive_time: string;
    bed_level_info: string;
    controlled_train_flag: string;
    country_flag: string;
    day_difference: string;
    dw_flag: string;
    end_station_name: string;
    end_station_telecode: string;
    from_station_name: string;
    from_station_no: string;
    from_station_telecode: string;
    gg_num: string;
    gr_num: string;
    is_support_card: string;
    lishi: string;
    local_arrive_time: string;
    local_start_time: string;
    qt_num: string;
    rw_num: string;
    rz_num: string;
    seat_discount_info: string;
    seat_types: string;
    srrb_num: string;
    start_station_name: string;
    start_station_telecode: string;
    start_time: string;
    start_train_date: string;
    station_train_code: string;
    swz_num: string;
    to_station_name: string;
    to_station_no: string;
    to_station_telecode: string;
    train_no: string;
    train_seat_feature: string;
    trms_train_flag: string;
    tz_num: string;
    wz_num: string;
    yb_num: string;
    yp_info: string;
    yw_num: string;
    yz_num: string;
    ze_num: string;
    zy_num: string;
};
