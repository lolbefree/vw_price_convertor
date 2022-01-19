#!/usr/bin/python
# -*- coding: utf-8 -*-
import math
import sys
from datetime import date, datetime
from pprint import pprint

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from collections import Counter
import sqlquerys
from converot_gui import Ui_MainWindow
import pyodbc
import not_for_git
import pandas as pd


class Convertor(QtWidgets.QMainWindow):
    def __init__(self):
        self.ui = Ui_MainWindow()
        super().__init__()
        self.ui.setupUi(self)
        self.now = datetime.now()
        self.today = date.today()
        self.server = not_for_git.db_server
        self.database = not_for_git.db_name
        self.username = not_for_git.db_user
        self.password = not_for_git.db_pw
        self.driver = '{SQL Server}'  # Driver you need to connect to the database
        self.port = '1433'
        self.name = ""
        self.if_in_base = False
        self.row_count = int()

        self.cnn = pyodbc.connect(
            'DRIVER=' + self.driver + ';PORT=port;SERVER=' + self.server + ';PORT=1443;DATABASE=' + self.database + ';UID=' + self.username +
            ';PWD=' + self.password)
        self.ui.centralwidget.setStyleSheet("background: #d6d6d6")
        #
        # for widget in [self.ui.Open_file_vw, self.ui.Open_file_sk, self.ui.RUN_sk, self.ui.RUN_vw]:
        #     widget.setStyleSheet("background: #f0f3f4")

        self.cursor = self.cnn.cursor()
        self.ui.Open_file_vw.clicked.connect(lambda x: self.showDialog())
        # self.ui.Open_file_sk.clicked.connect(lambda x: self.showDialog("sk"))
        self.ui.RUN_vw.clicked.connect(lambda x: self.parse_txt())

    def showDialog(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '*.txt')[0]
        name_index_ = fname.rfind("/")
        self.name = fname
        self.ui.name_file_vw.setText(fname[name_index_ + 1:])

    def check_float(self, potential_float):
        try:
            float(potential_float)
            return True
        except ValueError:
            return False

    def get_len_txt(self):
        with open(self.name) as incoming_file:
            self.row_count = len(incoming_file.readlines())
            return self.row_count - 4

    def discount_formula(self, num, disc):
        """считаем скидку и форматируем с нолями"""
        res = num * (1 - disc / 100)
        res = str(self.round_half_up(res, 2))
        res_dot_index = res.index(".")
        if len(res[res_dot_index + 1:]) == 1:
            res += "0"
        res = res.replace(".", "")
        res = "0" * (11 - len(res)) + res
        return res

    def parse_txt(self):
        """ открываем сплитим пробелы, после убераем пустые строки"""
        self.get_len_txt()
        self.last_row = open(self.name, "r").readlines()[-1].split(" ")
        self.create_modify_file = open(
            f"{self.name[:-4]}_converted_{self.today.strftime('%d_%m_%Y')}_{self.now.strftime('%H_%M')}_.txt", "w")

        with open(self.name) as incoming_file:
            income_data = list()
            income_data_without_space = list()
            first_two_lines = list()
            first_two_lines_modify = list()
            first_two_lines.append(incoming_file.readline().split(" "))
            first_two_lines.append(incoming_file.readline().split(" "))
            for i in first_two_lines:
                for j in i:
                    if j != "":
                        first_two_lines_modify.append(j)

            first_two_lines.clear()
            first_two_lines += [first_two_lines_modify[0]] + [
                first_two_lines_modify[1] + " " + first_two_lines_modify[2]] \
                               + [first_two_lines_modify[3] + " " + first_two_lines_modify[4]] + first_two_lines_modify[
                                                                                                 5:12] \
                               + [first_two_lines_modify[-4]] + [
                                   first_two_lines_modify[-3] + first_two_lines_modify[-2]] + [
                                   first_two_lines_modify[-1]]
            first_two_lines_modify.clear()

            for line in incoming_file.readlines():
                income_data += [line[5:19]] + [line[20:30]] + line[30:].split(" ")
            tmp_list = []
            for item in income_data:
                if item != "":
                    tmp_list.append(item)
                if item == "\n":
                    income_data_without_space.append(tmp_list.copy())
                    tmp_list.clear()
            get_last_row_sum = []
            for item in self.last_row:
                if item != "":
                    get_last_row_sum.append(item)

            checked_code_list = []
            for code in income_data_without_space:
                checked_code_list.append(code[0])

            res = list(self.cursor.execute(sqlquerys.check_in_base(checked_code_list)))
            checked_code_list.clear()
            cnt = 0
            while cnt != len(res):
                checked_code_list.append(res[cnt][0].replace(" ", ""))
                cnt += 1
            self.generate_multiply_string(income_data_without_space, checked_code_list, first_two_lines,
                                          get_last_row_sum)

    def round_half_up(self, n, decimals=0):
        multiplier = 10 ** decimals

        return math.floor(n * multiplier + 0.5) / multiplier

    def generate_multiply_string(self, income_data_without_space, checked_code_list, first_two_lines, get_last_row_sum):
        string_to_write = """\n"""
        vins = []
        vinl = []

        for item in income_data_without_space:
            vinl.append(item[0])
        for key, value in dict(Counter(vinl)).items():
            if value > 1:
                vins.append(key)
        list_with_index = []
        list_of_list_with_data = []
        for index, item in enumerate(income_data_without_space, 0):

            for vn in vins:
                if vn in item:
                    list_with_index.append(index)
                    list_of_list_with_data.append(income_data_without_space[index])

        def check_glue_list():
            df = pd.DataFrame(list_of_list_with_data)
            df[[3, 6]] = df[[3, 6]].astype("float")
            df[[3, 6]] = df.groupby([0, 9])[[3, 6]].transform('sum')
            df[[3, 6]] = df[[3, 6]].applymap('{:.2f}'.format)
            df[[3, 6]] = df[[3, 6]].astype("str")
            res = df.drop_duplicates().values.tolist()

            nlst = []
            for i in range(len(res) - 1):
                if res[i][0:10] == res[i + 1][0:10]:
                    nlst.append(res[i])

            for i in nlst:
                res.remove(i)

            for i in res:
                if i:
                    i[3] += "0"
                    i[6] += "0"
                    if i[-6] != "1":
                        i.insert(-6, "")
                        del i[-1]
                        if i[-1] != "\n":
                            i.append("\n")

            #
            # for i in res:
            #    print(i)

            for i in res:
                income_data_without_space.append(i)

            for del_i in list_of_list_with_data:
                income_data_without_space.remove(del_i)

        if list_of_list_with_data:
            check_glue_list()

        self.ui.progressBar_vw.setMaximum(self.row_count - 4 + 10)
        #
        # for row in income_data_without_space:
        #     print(row)
        for cnt, row in enumerate(income_data_without_space, 1):
            self.ui.progressBar_vw.setValue(cnt)
            if len(row) < 21 and row[9] == '0':
                row.insert(9, "     ")

            if row[0].replace(" ", "") in checked_code_list:

                row0 = row[0].replace(" ", "") + (" " * (14 - len(row[0].replace(" ", ""))))
            else:
                row0 = row[0]
            try:
                # print(sqlquerys.check_itemno(row[9], row[10]))
                res = list(self.cursor.execute(sqlquerys.check_itemno(row[9], row[10])))[0][0]
            except (IndexError, pyodbc.ProgrammingError):
                res = row0.replace(" ", "")
            if res.replace(" ", "") != row0.replace(" ", ""):
                row0 = res + (" " * (14 - len(res)))
            first_col = "I" + row0
            second_col = ("0" * (12 - len(row[3].replace(".", "") + first_two_lines[0])) +
                          row[3].replace(".", "")) + first_two_lines[0] + "             "
            third_col = first_two_lines[1] + "        "
            fourth_column = first_two_lines[2]

            fifth_column = self.add_spaces(first_two_lines[3], 21 - len(first_two_lines[3]))

            sixth_column = "XXX" + first_two_lines[5].replace(".", "") + first_two_lines[6].replace(".", "")
            sixth_column = self.add_spaces(sixth_column, 24 - len(sixth_column))
            seventh_column = self.add_spaces(first_two_lines[7], 12 - len(first_two_lines[7]))
            eighth_column = self.add_spaces(first_two_lines[8], 12 - len(first_two_lines[8]))
            ninth_column = self.add_spaces(first_two_lines[9], 12 - len(first_two_lines[9]))
            tenth_column = self.add_spaces(first_two_lines[10], 12 - len(first_two_lines[10]))
            eleventh_column = first_two_lines[11] + first_two_lines[12].replace("\n", "") + "XXX"
            eleventh_column = self.add_spaces(eleventh_column, 20 - len(eleventh_column))
            twelfth_column = str(cnt) + row[0] + " " * (int(14 - len(row0)))
            twelfth_column = self.add_spaces(twelfth_column, 18 - len(twelfth_column))
            thirteenth_column = row[1] + "          "
            fourteenth_column = row[2] + "0" * (7 - len(row[3].replace(".", ""))) + row[3].replace(".", "") + \
                                row[4] + str(self.discount_formula(float(row[5]), (float(row[8]))))

            tmp_sum = str(self.round_half_up(float(row[6]) * (1 - float(row[8]) / 100), 2))
            res_dot_index = tmp_sum.index(".")
            if len(tmp_sum[res_dot_index + 1:]) == 1:
                sum_with_disc = tmp_sum + "0"
            else:
                sum_with_disc = tmp_sum
            sum_with_disc = sum_with_disc.replace(".", "")
            fifteenth_column_count_zero = "0" * (11 - len(sum_with_disc)) + sum_with_disc
            fifteenth_column = row[6] + (row[7] if len(row[7]) == 2 else row[7] + " ") + \
                               row[8] + fifteenth_column_count_zero + row[9]
            fifteenth_column = (" " * (35 - len(fifteenth_column))) + fifteenth_column

            sixteenth_column = " " * (10 - len(row[10] + row[11])) + row[10] + row[11] + " " * 18 + row[12]

            sixteenth_column_spaces_after = (58 - len(sixteenth_column)) * " "
            seventeenth_column = sixteenth_column_spaces_after + row[13] + " " + row[14] + "               "

            eighteenth_column = "1      303" if row[15] == "1" else "       303"
            eighteenth_column += "   VW AG                                             " + row[
                -2] + "1XXX1" + (" " * (18 - len(get_last_row_sum[1] + get_last_row_sum[2])) +
                                 get_last_row_sum[1] + get_last_row_sum[2])

            string_to_write += f"""{first_col}{second_col}{third_col}{fourth_column}{fifth_column}{sixth_column}{seventh_column}{eighth_column}{ninth_column}{tenth_column}{eleventh_column}{twelfth_column}{thirteenth_column}{fourteenth_column}{fifteenth_column}{sixteenth_column}{seventeenth_column}{eighteenth_column}"""

        self.create_modify_file.write(string_to_write)

        self.create_modify_file.close()
        self.ui.progressBar_vw.setValue(self.ui.progressBar_vw.maximum())

    def add_spaces(self, string, len_str):
        return " " * len_str + string


def main():
    app = QApplication(sys.argv)
    w = Convertor()
    w.show()
    app.exec_()


if __name__ == '__main__':
    main()
