import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
import random
from math import pi, log10, cos, sin
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

    freq_start = FloatParameter('Start Frequency', units='Hz', default=100e3)
    freq_end = FloatParameter('End Frequency', units='Hz', default=20)
    points_per_decade = IntegerParameter('Points per decade', units=None, default=10)

    voltage_rms = FloatParameter('E_ac rms', units='mV', default=10)
    voltage_dcbias = FloatParameter('E_dc bias', units='V', default=1.5)

    DATA_COLUMNS = ['Frequency (Hz)', 'Impedance (ohm)', 'Phase Angle (deg)', 'Re[Z] (ohm)', 'Im[Z] (ohm)']

    def startup(self):

        self.lcrmeter = HP4284A("GPIB0::17::INSTR")
        self.lcrmeter.mode = "ZTD"
        self.lcrmeter.trigger_source = "BUS"

        self.lcrmeter.ac_voltage = self.voltage_rms/1000
        self.lcrmeter.bias_voltage = self.voltage_dcbias
        
        number_of_decades = log10(self.freq_start) - log10(self.freq_end)
        number_of_points = int(number_of_decades) * self.points_per_decade
        self.meas_frequencies = np.logspace(log10(self.freq_start), log10(self.freq_end),
                                            num=number_of_points,
                                            endpoint=True,
                                            base=10)

    def execute(self):

        self.lcrmeter.enable_bias()

        for freq in self.meas_frequencies:
            self.lcrmeter.frequency = freq
            z, theta_deg = self.lcrmeter.impedance
            theta_rad = theta_deg * pi / 180

            data = {
                'Frequency (Hz)': self.lcrmeter.frequency,
                'Impedance (ohm)': z,
                'Phase Angle (deg)': theta_deg,
                'Re[Z] (ohm)': z * cos(theta_rad),
                'Im[Z] (ohm)': z * sin(theta_rad)
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
            inputs=['sample', 'freq_start', 'freq_end', 'points_per_decade', 'voltage_rms', 'voltage_dcbias'],
            displays=['sample', 'freq_start', 'freq_end', 'points_per_decade', 'voltage_rms', 'voltage_dcbias'],
            x_axis='Re[Z] (ohm)',
            y_axis='Im[Z] (ohm)',
            hide_groups=False,
            directory_input=True
        )
        self.setWindowTitle('Electrochemical Impedance Spectroscopy')
        self.directory = r'C:/Users/16512/Desktop/Anupam/EIS Data'

    def queue(self):

        procedure = self.make_procedure()

        directory = self.directory
        prefix = "{Sample ID}_"
        prefix = replace_placeholders(string=prefix, procedure=procedure)
        filename = unique_filename(directory, prefix=prefix)

        title = "Electrochemical Impedance Spectroscopy -- Sample '{Sample ID}'"
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