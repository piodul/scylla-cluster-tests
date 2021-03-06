# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright (c) 2016 ScyllaDB

import os
import time

from sdcm.utils.common import FileFollowerThread


class CassandraStressExporter(FileFollowerThread):
    METRICS = {}

    def __init__(self, instance_name, metrics, cs_operation, cs_log_filename, loader_idx, cpu_idx):  # pylint: disable=too-many-arguments

        super(CassandraStressExporter, self).__init__()
        self.metrics = metrics
        self.cs_operation = cs_operation
        self.cs_log_filename = cs_log_filename
        gauge_name = 'collectd_cassandra_stress_%s_gauge' % self.cs_operation
        if gauge_name not in self.METRICS:
            self.METRICS[gauge_name] = self.metrics.create_gauge('collectd_cassandra_stress_%s_gauge' % self.cs_operation,
                                                                 'Gauge for cassandra stress metrics',
                                                                 ['cassandra_stress_%s' % self.cs_operation, 'instance', 'loader_idx', 'cpu_idx', 'type'])
        self.cs_metric = self.METRICS[gauge_name]
        self.instance_name = instance_name
        self.loader_idx = loader_idx
        self.cpu_idx = cpu_idx

    def set_metric(self, name, value):
        self.cs_metric.labels(0, self.instance_name, self.loader_idx, self.cpu_idx, name).set(value)

    def clear_metrics(self):
        if self.cs_metric:
            for metric_name in ['ops', 'lat_mean', 'lat_med', 'lat_perc_95', 'lat_perc_99', 'lat_perc_999', 'lat_max', 'errors']:
                self.set_metric(metric_name, 0.0)

    def run(self):
        while not self.stopped():
            exists = os.path.isfile(self.cs_log_filename)
            if not exists:
                time.sleep(0.5)
                continue

            for line in self.follow_file(self.cs_log_filename):
                if self.stopped():
                    break

                if not 'total,' in line:
                    continue

                cols = [element.strip() for element in line.split(',')]

                ops = float(cols[2])
                lat_mean = float(cols[5])
                lat_med = float(cols[6])
                lat_perc_95 = float(cols[7])
                lat_perc_99 = float(cols[8])
                lat_perc_999 = float(cols[9])
                lat_max = float(cols[10])
                errors = int(cols[13])

                self.set_metric('ops', ops)
                self.set_metric('lat_mean', lat_mean)
                self.set_metric('lat_med', lat_med)
                self.set_metric('lat_perc_95', lat_perc_95)
                self.set_metric('lat_perc_99', lat_perc_99)
                self.set_metric('lat_perc_999', lat_perc_999)
                self.set_metric('lat_max', lat_max)
                self.set_metric('errors', errors)
