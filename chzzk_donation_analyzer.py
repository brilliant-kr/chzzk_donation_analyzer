import sys
import json
import webbrowser
import platform
from collections import defaultdict
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QMessageBox, QSplitter, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.font_manager as fm

def setup_matplotlib_font():
    system = platform.system()
    if system == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
    elif system == 'Darwin':
        plt.rcParams['font.family'] = 'AppleGothic'
    else:  # Linux
        plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False

setup_matplotlib_font()

class DonationAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = None
        self.analysis_results = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle('치지직 후원 분석기')
        self.setGeometry(100, 100, 1400, 900)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        input_label = QLabel('JSON 데이터 입력:')
        input_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        main_layout.addWidget(input_label)

        self.json_input = QTextEdit()
        self.json_input.setPlaceholderText('{\n  "code": 200,\n  "message": null,\n  "content": {\n    "page": 0,\n    "size": 1000,\n    "totalCount": 158,\n    "data": [\n      {\n        "purchaseDate": "2025-11-20 19:36:43",\n        "payAmount": 10000,\n        "channelName": "채널명",\n        ...\n      }\n    ]\n  }\n}')
        self.json_input.setMaximumHeight(200)
        main_layout.addWidget(self.json_input)

        button_layout = QHBoxLayout()

        self.open_api_btn = QPushButton('치지직 API에서 데이터 가져오기')
        self.open_api_btn.clicked.connect(self.open_chzzk_api)
        self.open_api_btn.setStyleSheet('QPushButton { background-color: #FF6B35; color: white; font-size: 14px; padding: 10px; }')
        button_layout.addWidget(self.open_api_btn)

        self.load_file_btn = QPushButton('파일에서 불러오기')
        self.load_file_btn.clicked.connect(self.load_from_file)
        button_layout.addWidget(self.load_file_btn)

        self.analyze_btn = QPushButton('분석 시작')
        self.analyze_btn.clicked.connect(self.analyze_data)
        self.analyze_btn.setStyleSheet('QPushButton { background-color: #4CAF50; color: white; font-size: 14px; padding: 10px; }')
        button_layout.addWidget(self.analyze_btn)

        self.clear_btn = QPushButton('초기화')
        self.clear_btn.clicked.connect(self.clear_input)
        button_layout.addWidget(self.clear_btn)

        main_layout.addLayout(button_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.summary_tab = QWidget()
        self.channel_tab = QWidget()
        self.time_tab = QWidget()
        self.graph_tab = QWidget()

        self.tabs.addTab(self.summary_tab, '요약')
        self.tabs.addTab(self.channel_tab, '채널별')
        self.tabs.addTab(self.time_tab, '시간별')
        self.tabs.addTab(self.graph_tab, '그래프')

        self.setup_summary_tab()
        self.setup_channel_tab()
        self.setup_time_tab()
        self.setup_graph_tab()

    def setup_summary_tab(self):
        layout = QVBoxLayout()
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont('Courier', 11))
        layout.addWidget(self.summary_text)
        self.summary_tab.setLayout(layout)

    def setup_channel_tab(self):
        layout = QVBoxLayout()
        self.channel_table = QTableWidget()
        self.channel_table.setColumnCount(3)
        self.channel_table.setHorizontalHeaderLabels(['순위', '채널명', '총 후원 금액'])
        self.channel_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.channel_table)
        self.channel_tab.setLayout(layout)

    def setup_time_tab(self):
        layout = QVBoxLayout()

        # 월별 테이블
        month_label = QLabel('월별 후원 금액:')
        month_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        layout.addWidget(month_label)

        self.month_table = QTableWidget()
        self.month_table.setColumnCount(3)
        self.month_table.setHorizontalHeaderLabels(['월', '후원 금액', '후원 건수'])
        layout.addWidget(self.month_table)

        # 요일별 테이블
        weekday_label = QLabel('요일별 평균 후원 금액:')
        weekday_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        layout.addWidget(weekday_label)

        self.weekday_table = QTableWidget()
        self.weekday_table.setColumnCount(4)
        self.weekday_table.setHorizontalHeaderLabels(['요일', '평균 금액', '총 금액', '건수'])
        layout.addWidget(self.weekday_table)

        self.time_tab.setLayout(layout)

    def setup_graph_tab(self):
        layout = QVBoxLayout()
        self.figure = Figure(figsize=(15, 10))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.graph_tab.setLayout(layout)

    def open_chzzk_api(self):
        url = 'https://api.chzzk.naver.com/commercial/v1/product/purchase/history?page=0&size=5000&searchYear=2025'
        webbrowser.open(url)
        QMessageBox.information(self, '안내',
            '브라우저에서 치지직 API가 열렸습니다.\n\n'
            '1. 브라우저에 표시된 JSON 데이터를 전체 복사하세요 (Ctrl+A, Ctrl+C)\n'
            '2. 이 프로그램의 입력창에 붙여넣으세요 (Ctrl+V)\n'
            '3. "분석 시작" 버튼을 클릭하세요')

    def load_from_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '파일 열기', '', 'JSON Files (*.json)')
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.json_input.setPlainText(content)
                    QMessageBox.information(self, '성공', '파일을 불러왔습니다.')
            except Exception as e:
                QMessageBox.critical(self, '오류', f'파일을 읽는 중 오류가 발생했습니다:\n{str(e)}')

    def clear_input(self):
        self.json_input.clear()
        self.summary_text.clear()
        self.channel_table.setRowCount(0)
        self.month_table.setRowCount(0)
        self.weekday_table.setRowCount(0)
        self.figure.clear()
        self.canvas.draw()

    def analyze_data(self):
        try:
            # JSON 파싱
            json_text = self.json_input.toPlainText().strip()
            if not json_text:
                QMessageBox.warning(self, '경고', 'JSON 데이터를 입력해주세요.')
                return

            parsed_data = json.loads(json_text)

            # {"code":200,"content":{"data":[...]}} 형식만 지원
            if 'content' not in parsed_data or 'data' not in parsed_data['content']:
                QMessageBox.warning(self, '경고', 'JSON 형식이 올바르지 않습니다.\n"content.data" 배열이 필요합니다.')
                return

            data_array = parsed_data['content']['data']

            if not isinstance(data_array, list):
                QMessageBox.warning(self, '경고', 'data가 배열 형식이 아닙니다.')
                return

            self.data = {'data': data_array}

            # 분석 수행
            self.perform_analysis()

            # 결과 표시
            self.display_summary()
            self.display_channel_table()
            self.display_time_tables()
            self.display_graphs()

            QMessageBox.information(self, '완료', f'분석이 완료되었습니다.\n총 {len(self.data["data"])}건의 후원 데이터를 분석했습니다.')

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, '오류', f'JSON 파싱 오류:\n{str(e)}')
        except Exception as e:
            QMessageBox.critical(self, '오류', f'분석 중 오류가 발생했습니다:\n{str(e)}')

    def perform_analysis(self):
        weekday_names = ['월', '화', '수', '목', '금', '토', '일']

        channel_sum = defaultdict(int)
        year_sum = defaultdict(int)
        month_sum = defaultdict(int)
        month_count = defaultdict(int)
        weekday_sum = defaultdict(int)
        weekday_count = defaultdict(int)
        max_donation = None

        for item in self.data['data']:
            channel_name = item['channelName']
            pay_amount = item['payAmount']
            purchase_date = item['purchaseDate']

            dt = datetime.strptime(purchase_date, "%Y-%m-%d %H:%M:%S")
            year = dt.strftime("%Y")
            year_month = dt.strftime("%Y-%m")
            weekday = weekday_names[dt.weekday()]

            channel_sum[channel_name] += pay_amount
            year_sum[year] += pay_amount
            month_sum[year_month] += pay_amount
            month_count[year_month] += 1
            weekday_sum[weekday] += pay_amount
            weekday_count[weekday] += 1

            if max_donation is None or pay_amount > max_donation['payAmount']:
                max_donation = item

        self.analysis_results = {
            'channel_sum': channel_sum,
            'year_sum': year_sum,
            'month_sum': month_sum,
            'month_count': month_count,
            'weekday_sum': weekday_sum,
            'weekday_count': weekday_count,
            'max_donation': max_donation,
            'total_amount': sum(channel_sum.values()),
            'total_count': len(self.data['data'])
        }

    def display_summary(self):
        results = self.analysis_results

        summary = f"""
{'='*60}
최대 단건 후원 정보
{'='*60}
채널명: {results['max_donation']['channelName']}
후원 금액: {results['max_donation']['payAmount']:,}원
후원 날짜: {results['max_donation']['purchaseDate']}
후원 타입: {results['max_donation']['donationType']}
"""
        if results['max_donation']['donationText']:
            summary += f"메시지: {results['max_donation']['donationText']}\n"

        summary += f"""
{'='*60}
전체 통계
{'='*60}
총 후원 금액: {results['total_amount']:,}원
총 후원 건수: {results['total_count']:,}건
평균 후원 금액: {results['total_amount'] / results['total_count']:,.0f}원

{'='*60}
연도별 후원 금액
{'='*60}
"""
        for year in sorted(results['year_sum'].keys(), reverse=True):
            summary += f"[{year}년] {results['year_sum'][year]:,}원\n"

        # 스폰서
        summary +=  f"""








{'-'*60}
Special Thanks to
    치지직 "일없는사람"
{'-'*60}
        """

        self.summary_text.setPlainText(summary)

    def display_channel_table(self):
        channel_sum = self.analysis_results['channel_sum']
        sorted_channels = sorted(channel_sum.items(), key=lambda x: x[1], reverse=True)

        self.channel_table.setRowCount(len(sorted_channels))

        for i, (channel, amount) in enumerate(sorted_channels):
            self.channel_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.channel_table.setItem(i, 1, QTableWidgetItem(channel))
            self.channel_table.setItem(i, 2, QTableWidgetItem(f"{amount:,}원"))

    def display_time_tables(self):
        results = self.analysis_results

        # 월별 테이블
        month_sum = results['month_sum']
        month_count = results['month_count']
        sorted_months = sorted(month_sum.keys(), reverse=True)

        self.month_table.setRowCount(len(sorted_months))

        for i, month in enumerate(sorted_months):
            self.month_table.setItem(i, 0, QTableWidgetItem(month))
            self.month_table.setItem(i, 1, QTableWidgetItem(f"{month_sum[month]:,}원"))
            self.month_table.setItem(i, 2, QTableWidgetItem(f"{month_count[month]}건"))

        # 요일별 테이블
        weekday_sum = results['weekday_sum']
        weekday_count = results['weekday_count']
        weekday_order = ['월', '화', '수', '목', '금', '토', '일']

        self.weekday_table.setRowCount(len(weekday_order))

        for i, weekday in enumerate(weekday_order):
            if weekday in weekday_sum:
                avg = weekday_sum[weekday] / weekday_count[weekday]
                self.weekday_table.setItem(i, 0, QTableWidgetItem(f"{weekday}요일"))
                self.weekday_table.setItem(i, 1, QTableWidgetItem(f"{avg:,.0f}원"))
                self.weekday_table.setItem(i, 2, QTableWidgetItem(f"{weekday_sum[weekday]:,}원"))
                self.weekday_table.setItem(i, 3, QTableWidgetItem(f"{weekday_count[weekday]}건"))

    def display_graphs(self):
        results = self.analysis_results
        self.figure.clear()

        # 1. 채널별 TOP 10
        ax1 = self.figure.add_subplot(2, 3, 1)
        channel_sum = results['channel_sum']
        top_channels = dict(sorted(channel_sum.items(), key=lambda x: x[1], reverse=True)[:10])
        bars1 = ax1.barh(list(top_channels.keys()), list(top_channels.values()), color='skyblue')
        ax1.set_xlabel('후원 금액 (원)')
        ax1.set_title('채널별 후원 금액 TOP 10')
        ax1.invert_yaxis()
        # 숫자 레이블 추가
        for i, v in enumerate(top_channels.values()):
            ax1.text(v, i, f' {v:,}원', va='center', fontsize=8)

        # 2. 연도별
        ax2 = self.figure.add_subplot(2, 3, 2)
        year_sum = results['year_sum']
        years = sorted(year_sum.keys())
        year_amounts = [year_sum[y] for y in years]
        bars2 = ax2.bar(years, year_amounts, color='lightgreen')
        ax2.set_xlabel('연도')
        ax2.set_ylabel('후원 금액 (원)')
        ax2.set_title('연도별 후원 금액')
        # 숫자 레이블 추가
        for i, v in enumerate(year_amounts):
            ax2.text(i, v, f'{v:,}원', ha='center', va='bottom', fontsize=9)

        # 3. 월별
        ax3 = self.figure.add_subplot(2, 3, 3)
        month_sum = results['month_sum']
        months = sorted(month_sum.keys())
        month_amounts = [month_sum[m] for m in months]
        ax3.plot(months, month_amounts, marker='o', linewidth=2, markersize=8, color='coral')
        ax3.set_xlabel('월')
        ax3.set_ylabel('후원 금액 (원)')
        ax3.set_title('월별 후원 금액 추이')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)

        # 4. 요일별 평균
        ax4 = self.figure.add_subplot(2, 3, 4)
        weekday_order = ['월', '화', '수', '목', '금', '토', '일']
        weekday_sum = results['weekday_sum']
        weekday_count = results['weekday_count']
        weekday_avg = [weekday_sum.get(w, 0) / weekday_count.get(w, 1) if weekday_count.get(w, 0) > 0 else 0 for w in weekday_order]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE']
        bars4 = ax4.bar(weekday_order, weekday_avg, color=colors)
        ax4.set_xlabel('요일')
        ax4.set_ylabel('평균 후원 금액 (원)')
        ax4.set_title('요일별 평균 후원 금액')
        # 숫자 레이블 추가
        for i, v in enumerate(weekday_avg):
            if v > 0:
                ax4.text(i, v, f'{v:,.0f}원', ha='center', va='bottom', fontsize=8)

        # 5. 채널별 비율
        ax5 = self.figure.add_subplot(2, 3, 5)
        top5_channels = dict(sorted(channel_sum.items(), key=lambda x: x[1], reverse=True)[:5])
        other_amount = sum(channel_sum.values()) - sum(top5_channels.values())
        if other_amount > 0:
            top5_channels['기타'] = other_amount
        ax5.pie(top5_channels.values(), labels=top5_channels.keys(), autopct='%1.1f%%', startangle=90)
        ax5.set_title('채널별 후원 비율 (TOP 5)')

        # 6. 월별 건수
        ax6 = self.figure.add_subplot(2, 3, 6)
        month_count = results['month_count']
        months_count = sorted(month_count.keys())
        counts = [month_count[m] for m in months_count]
        bars6 = ax6.bar(months_count, counts, color='mediumpurple')
        ax6.set_xlabel('월')
        ax6.set_ylabel('후원 건수')
        ax6.set_title('월별 후원 건수')
        ax6.tick_params(axis='x', rotation=45)
        # 숫자 레이블 추가
        for i, v in enumerate(counts):
            ax6.text(i, v, str(v), ha='center', va='bottom', fontsize=8)

        self.figure.text(0.5, 0.5, '탁월합니다',
                        fontsize=40, color='gray', alpha=0.1,
                        ha='center', va='center', rotation=30,
                        transform=self.figure.transFigure, zorder=0)

        self.figure.tight_layout()
        self.canvas.draw()



def main():
    app = QApplication(sys.argv)
    window = DonationAnalyzer()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
