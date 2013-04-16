function (key, values, rereduce) {
    result = {};
    if (rereduce) {
        for (dict in values) {
            for (key in values[dict]) {
                if (!(key in result)) result[key] = 0;
                result[key] += values[dict][key];
            }
        }
        return result;
    }
    for (value in values) {
        if (!(values[value] in result)) result[values[value]] = 0;
        result[values[value]]++;
    }
    return result;
}
