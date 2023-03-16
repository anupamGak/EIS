import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
import random
from math import pi, log10
import numpy as np
from time import sleep
#from pymeasure.instruments.agilent import AgilentE4980
from hp4284a import HP4284A
from pymeasure.log import console_log
from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Procedure, Results, unique_filename, replace_placeholders
from pymeasure.experiment import FloatParameter, Parameter, IntegerParameter


class EISProcedure(Procedure):


    sample = Parameter('Sample ID')

    freq_start = FloatParameter('Starting Frequency', units='Hz')
    freq_end = FloatParameter('Ending Frequency', units='Hz')
    points_per_decade = IntegerParameter('Points per decade', units=None)

    voltage_rms = FloatParameter('AC Voltage rms', units='mV')
    ocv = FloatParameter('OCV', units='V')

    DATA_COLUMNS = ['Frequency (Hz)', 'Impedance (Ω)', 'Phase Angle (deg)', 'Re[Z] (Ω)', 'Im[Z] (Ω)']

    def startup(self):

        self.lcrmeter = HP4284A("GPIB0::17::INSTR")
        self.lcrmeter.mode = "ZTD"
        self.lcrmeter.trigger_source = "BUS"

        self.lcrmeter.ac_voltage = self.voltage_rms
        self.lcrmeter.bias_voltage = self.ocv
        
        number_of_decades = log10(self.freq_start) - log10(self.freq_end)
        number_of_points = int(number_of_decades) * self.points_per_decade
        self.meas_frequencies = np.logspace(log10(self.freq_start), log10(self.freq_end), num=npoints, endpoint=True, base=10)

    def execute(self):

        self.lcrmeter.enable_bias()

        for freq in self.meas_frequencies:
            self.lcrmeter.frequency = freq
            z, theta_deg = self.lcrmeter.impedance
            theta_rad = theta * pi / 180

            data = {
            'Frequency (Hz)': freq,
            'Impedance (Ω)': z,
            'Phase Angle (deg)': theta_deg,
            'Re[Z] (Ω)': z * cos(theta_rad),
            'Im[Z] (Ω)': z * sin(theta_rad)
            }
            self.emit('results', data)
            sleep(0.5)
            if self.should_stop():
                log.info("[EIS] User aborted the EIS procedure")
                break


class MainWindow(ManagedWindow):


    def __init__(self):
        super().__init__(
            procedure_class=EISProcedure,
            inputs=['freq_start', 'freq_end', 'points_per_decade', 'voltage_rms', 'ocv'],
            displays=['freq_start', 'freq_end', 'points_per_decade', 'voltage_rms', 'ocv'],
            x_axis='Re[Z] (Ω)',
            y_axis='Im[Z] (Ω)',
            hide_groups=False,
            directory_input=True
        )
        self.setWindowTitle('Electrochemical Impedance Spectroscopy')
        self.directory = r'D:/Anupam/EIS Data'

    def queue(self):

        procedure = self.make_procedure()

        directory = self.directory
        prefix = "{Sample ID}_"
        prefix = replace_placeholders(string=prefix, procedure=procedure)
        filename = unique_filename(directory, prefix=prefix)

        title = "Electrochemical Impedance Spectroscopy -- Sample {Sample ID}"
        title = replace_placeholders(string=title, procedure=procedure)
        self.setWindowTitle(title)

        results = Results(procedure, filename)
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())