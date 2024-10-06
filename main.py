import flet as ft
from tinydb import TinyDB, Query
from datetime import datetime, date
import os
# Initialize database
db = TinyDB('expense_db.json')

# Helper functions
def get_days_in_month(year, month):
    return (date(year, month % 12 + 1, 1) - date(year, month, 1)).days
def get_db_last_modified_time():
    return datetime.fromtimestamp(os.path.getmtime('expense_db.json')).strftime("%Y-%m-%d %H:%M:%S")

# Main application class
class ExpenseTrackerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self.current_week = 1
        self.zoom_level = 1
        self.min_zoom = 0.5
        self.max_zoom = 2
        self.chart_type = 'bar_chart'
        self.chart = None
        self.chart_with_zoom = None
        self.history_sort_order = "newest_first"
        self.sections = self.load_sections()  # Load sections from database
        self.setup_ui_components()
        self.update_results()

    def setup_page(self):
        self.page.title = "MoneyFlexerski"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1000
        self.page.window.height = 800

        self.page.bgcolor = ft.colors.TRANSPARENT
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(
                src=f"assets/pexels-sagui-andrea-200115-618833.jpg",
                fit=ft.ImageFit.COVER,
                opacity=0.2,
            ),
            gradient=ft.LinearGradient(
                colors=[ft.colors.BROWN, ft.colors.BLACK],
                stops=[0, 1],
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
            ),
        )

    def create_chart(self):
        if self.chart_type == 'bar_chart':
            self.chart = self.create_bar_chart()
            self.update_chart()  # Update the chart with data
        elif self.chart_type == 'line_chart':
            self.chart = self.create_line_chart()
            self.chart_with_zoom.controls = []  # Remove any zoom/navigation controls for line chart
        else:
            self.chart = None

        if self.chart_with_zoom:
            self.chart_with_zoom.controls = [self.chart] if self.chart else []
            self.page.update()  # Update the page to reflect the changes
    def setup_ui_components(self):
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Navigation buttons in a horizontally scrollable row
        self.navigation_buttons = ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(text=" 🎛️", on_click=self.show_dashboard, height=50),
                    ft.ElevatedButton(text=" 📜", on_click=self.show_history, height=50),
                    ft.ElevatedButton(text="📊", on_click=self.show_charts, height=50),
                    ft.ElevatedButton(text="📂", on_click=self.show_sections, height=50),
                    # Add more buttons if needed...
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.ALWAYS  # Enable horizontal scrolling
            ),
            padding=ft.padding.only(top=40, left=10, right=10, bottom=10),
            alignment=ft.alignment.top_center
        )
        self.navigation_buttons_dashboard = ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(text=" [🎛️]", on_click=self.show_dashboard, height=50, bgcolor=ft.colors.AMBER_200),
                    ft.ElevatedButton(text=" 📜", on_click=self.show_history, height=50),
                    ft.ElevatedButton(text="📊", on_click=self.show_charts, height=50),
                    ft.ElevatedButton(text="📂", on_click=self.show_sections, height=50),
                    # Add more buttons if needed...
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.ALWAYS  # Enable horizontal scrolling
            ),
            padding=ft.padding.only(top=40, left=10, right=10, bottom=10),
            alignment=ft.alignment.top_center
        )

        self.navigation_buttons_sections = ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(text=" 🎛️", on_click=self.show_dashboard, height=50),
                    ft.ElevatedButton(text=" 📜", on_click=self.show_history, height=50),
                    ft.ElevatedButton(text="📊", on_click=self.show_charts, height=50),
                    ft.ElevatedButton(text="[📂]", on_click=self.show_sections, height=50, bgcolor=ft.colors.AMBER_200),
                    # Add more buttons if needed...
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.ALWAYS  # Enable horizontal scrolling
            ),
            padding=ft.padding.only(top=40, left=10, right=10, bottom=10),
            alignment=ft.alignment.top_center
        )
        self.navigation_buttons_history = ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(text=" 🎛️", on_click=self.show_dashboard, height=50),
                    ft.ElevatedButton(text=" [📜]", on_click=self.show_history, height=50, bgcolor=ft.colors.AMBER_200),
                    ft.ElevatedButton(text="📊", on_click=self.show_charts, height=50),
                    ft.ElevatedButton(text="📂", on_click=self.show_sections, height=50),
                    # Add more buttons if needed...
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.ALWAYS  # Enable horizontal scrolling
            ),
            padding=ft.padding.only(top=40, left=10, right=10, bottom=10),
            alignment=ft.alignment.top_center
        )
        self.navigation_buttons_chart = ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(text=" 🎛️", on_click=self.show_dashboard, height=50),
                    ft.ElevatedButton(text=" 📜", on_click=self.show_history, height=50),
                    ft.ElevatedButton(text="[📊]", on_click=self.show_charts, height=50, bgcolor=ft.colors.AMBER_200),
                    ft.ElevatedButton(text="📂", on_click=self.show_sections, height=50),
                    # Add more buttons if needed...
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
                scroll=ft.ScrollMode.ALWAYS  # Enable horizontal scrolling
            ),
            padding=ft.padding.only(top=40, left=10, right=10, bottom=10),
            alignment=ft.alignment.top_center
        )

        # Year dropdown
        self.year_dropdown = ft.Dropdown(
            label="Year",
            options=[ft.dropdown.Option(str(year)) for year in range(current_year - 5, current_year + 6)],
            value=str(current_year),
            width=100,
            on_change=self.update_results
        )

        # Month dropdown
        self.month_dropdown = ft.Dropdown(
            label="Month",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 13)],
            value=str(current_month),
            width=100,
            on_change=self.update_results
        )

        # Income input and button
        self.income_input = ft.TextField(label="Monthly Income", width=200)
        self.income_button = ft.ElevatedButton(text="Save Income", on_click=self.save_income)
        self.income_result = ft.Text(size=30)

        # Expense input, day dropdown, and button
        self.expense_input = ft.TextField(label="Expense Amount", width=200)
        self.day_dropdown = ft.Dropdown(
            label="Day",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 32)],
            width=100
        )
        self.expense_button = ft.ElevatedButton(text="Save Expense", on_click=self.save_expense)
        self.expense_result = ft.Text(size=30)

        # Additional earning input and button
        self.additional_earning_input = ft.TextField(label="Additional Earning", width=200)
        self.additional_earning_day_dropdown = ft.Dropdown(
            label="Day",
            options=[ft.dropdown.Option(str(i)) for i in range(1, 32)],
            width=100
        )
        self.additional_earning_button = ft.ElevatedButton(text="Save Additional Earning", on_click=self.save_additional_earning)
        self.additional_earning_result = ft.Text(size=30)

        # Balance result
        self.balance_result = ft.Text(size=30)

        # Chart
        self.chart = self.create_chart()  # Ensure chart is created based on default type
        self.chart_with_zoom = ft.Column(
            [self.chart] if self.chart else [],  # Update to show the chart only if it exists
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Page title
        self.page_title = ft.Text("Info as in numbers:", size=20, weight=ft.FontWeight.BOLD)
        
        # self.sections_button = ft.ElevatedButton(text="Sections", on_click=self.show_sections, height=50)
        # self.navigation_buttons.content.controls.append(self.sections_button)

        # Create Sections page content
        self.sections_content = ft.Column([
            self.navigation_buttons_sections,
            ft.Text("Sections", size=30, weight=ft.FontWeight.BOLD),
            self.create_sections_layout()
        ], alignment=ft.MainAxisAlignment.START, expand=True, scroll=ft.ScrollMode.AUTO)
        
        
        # Main layout for dashboard
        self.dashboard_content = content = ft.Column([


            self.navigation_buttons_dashboard,
            ft.Row([self.year_dropdown, self.month_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.income_input, self.income_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.expense_input, self.day_dropdown, self.expense_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.additional_earning_input, self.additional_earning_day_dropdown, self.additional_earning_button], alignment=ft.MainAxisAlignment.CENTER),
            self.expense_result,
            self.income_result,
            self.additional_earning_result,
            self.balance_result,

            self.page_title
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        # Main layout for history

        # Update history content to include the sort dropdown
        self.history_list_view = ft.ListView(expand=1, spacing=10, padding=20)
        self.history_sort_dropdown = ft.Dropdown(
            label="Sort History",
            options=[
                ft.dropdown.Option("Newest First"),
                ft.dropdown.Option("Oldest First"),
                ft.dropdown.Option("Highest Amount"),
                ft.dropdown.Option("Lowest Amount"),
            ],
            value="Newest First",
            width=200,
            on_change=self.update_history_sort,
        )
        self.fancy_button = ft.ElevatedButton(
            text="Save Expense/Earning",
            on_click=self.save_expense_or_earning,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.HOVERED: ft.colors.WHITE,
                    ft.ControlState.DEFAULT: ft.colors.BLACK,
                },
                bgcolor={
                    ft.ControlState.HOVERED: ft.colors.GREEN,
                    ft.ControlState.DEFAULT: ft.colors.PURPLE,
                },
                padding=20,

            ),
        )

        self.expense_result = ft.Text(size=30, color=ft.colors.RED)
        self.additional_earning_result = ft.Text(size=30, color=ft.colors.ORANGE)
        self.balance_result = ft.Text(size=30, color=ft.colors.BLUE)

        # Page title
        #self.page_title = ft.Text("Click here if you want to support the app", size=20, weight=ft.FontWeight.BOLD)
        self.page_title = ft.GestureDetector(
            content=ft.Text("->🙃Consider donating🙂<-", size=20, weight=ft.FontWeight.BOLD),
            on_tap=self.show_support_alert  # Call the method to show alert on tap/click
        )
        # Main layout for dashboard
        self.dashboard_content = ft.Column([

            self.navigation_buttons_dashboard,
            ft.Row([self.year_dropdown, self.month_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.ListView(
                [

                    ft.Row([self.income_input, self.income_button], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.expense_input, self.day_dropdown], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.additional_earning_input, self.additional_earning_day_dropdown], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.fancy_button], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.income_result], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.additional_earning_result], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.expense_result], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.balance_result], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.page_title], alignment=ft.MainAxisAlignment.CENTER),
                                                                        ft.Row([ft.Text("MoneyFlexerski(money tracking by furime)")], alignment=ft.MainAxisAlignment.CENTER ),

                ],
                spacing=5,
                padding=10,
                expand=True,
            )
        ], 
        alignment=ft.MainAxisAlignment.START,
        expand=True
        )

        # Adjust the size of input fields and buttons
        for widget in [self.income_input, self.expense_input, self.additional_earning_input, 
                    self.income_button, self.fancy_button, self.day_dropdown, 
                    self.additional_earning_day_dropdown]:
            if isinstance(widget, ft.TextField):
                widget.width = 150  # Adjust width as needed
                widget.height = 40  # Adjust height as needed
            elif isinstance(widget, ft.Dropdown):
                widget.width = 100  # Adjust width as needed
            elif isinstance(widget, ft.ElevatedButton):
                widget.width = 200  # Adjust width as needed
                widget.height = 75  # Adjust height as needed

        # Adjust the size of result text
        for widget in [self.income_result, self.additional_earning_result, 
                    self.expense_result, self.balance_result, self.page_title]:
            widget.size = 20  # Adjust font size as needed
        # Update history content to include the sort dropdown
        self.history_content = ft.Column([
            self.navigation_buttons_history,
            self.history_sort_dropdown,
            self.history_list_view,
        ], expand=True)



        # Main layout for charts
        self.charts_content = ft.Column([
            self.navigation_buttons_chart,
            self.create_chart_type_dropdown(),  # Dropdown for chart types
            self.chart_with_zoom,  # Show the chart
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        # Create a separate container for navigation buttons
        self.navigation_container = ft.Container()

        # Add initial dashboard content
        self.page.add(self.dashboard_content)
    def update_history_sort(self, e):
        self.history_sort_order = e.control.value.lower().replace(" ", "_")
        self.update_history()  # This will now refresh the table
        self.page.update()  # Ensure the page updates to reflect the changes
    def show_support_alert(self, e):
        # Support options array (for example, donation links or texts)
        support_options = [
            {"label": "[Polish] Bank ", "text": "PL80 1140 2004 0000 3602 7931 9635"},
            {"label": "Paypal", "text": "https://www.paypal.com/paypalme/Furime"},
           
        ]

        # Create a list of clickable support options
        support_items = [
            ft.GestureDetector(
                content=ft.Text(option["label"], size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                on_tap=lambda e, option=option: self.copy_to_clipboard(option["text"])  # Copy to clipboard on click
            )
            for option in support_options
        ]

        # Create a closable alert dialog
        support_dialog = ft.AlertDialog(
            title=ft.Text("Support project"),
            content=ft.Column(
                controls=[

                    ft.Text("Click on the options below to copy the details:", size=20),
                    ft.Text("Contact: remusmaluss@gmail.com")
                ] + support_items,  # Add the list of support options
                alignment=ft.MainAxisAlignment.START
            ),
            actions=[
                ft.TextButton("Close", on_click=self.close_alert)  # Button to close the alert
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Show the dialog
        self.page.dialog = support_dialog
        support_dialog.open = True
        self.page.update()
    def copy_to_clipboard(self, text):
        self.page.set_clipboard(text)  # Copy the text to the clipboard
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Copied: {text}"),open=True, bgcolor=ft.colors.GREEN )  # Show a snackbar for confirmation
        self.page.update()

    def close_alert(self, e):
        self.page.dialog.open = False  # Close the dialog
        self.page.update()
    def show_dashboard(self, e):
        self.page.clean()
        self.page.add(self.dashboard_content)
    def load_sections(self):
        sections = db.table('sections').all()
        return sections if sections else []

    def save_sections(self):
        db.table('sections').truncate()
        db.table('sections').insert_multiple(self.sections)

    def create_sections_layout(self):
        sections_layout = ft.Column([], scroll=ft.ScrollMode.AUTO)
        for section in self.sections:
            section_card = self.create_section_card(section)
            sections_layout.controls.append(section_card)
        
        # Add a button to create a new section
        new_section_button = ft.ElevatedButton(
            text="Add New Section",
            on_click=self.add_new_section
        )
        sections_layout.controls.append(new_section_button)
        
        return sections_layout

    def create_section_card(self, section):
        balance = section['balance']
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(section['name'], size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Balance: ${balance:.2f}", size=16),
                    ft.Row([
                        ft.TextField(label="Amount", width=150),
                        ft.ElevatedButton(text="Add", on_click=lambda _: self.add_to_section(section, 'add')),
                        ft.ElevatedButton(text="Subtract", on_click=lambda _: self.add_to_section(section, 'subtract')),
                    ]),
                    ft.ElevatedButton(text="View History", on_click=lambda _: self.show_section_history(section)),
                ]),
                padding=10
            ),
            margin=10
        )

    def add_to_section(self, section, operation):
        amount_field = self.find_amount_field(section['name'])
        try:
            amount = float(amount_field.value)
            year = int(self.year_dropdown.value)
            month = int(self.month_dropdown.value)
            day = date.today().day
            
            if operation == 'add':
                section['balance'] += amount
            else:
                section['balance'] -= amount
            
            db.insert({
                'type': 'section_entry', 
                'section': section['name'], 
                'amount': amount if operation == 'add' else -amount, 
                'day': day, 
                'year': year, 
                'month': month
            })
            
            self.save_sections()
            self.update_sections_layout()
            amount_field.value = ""
        except ValueError:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please enter a valid number"))
            self.page.snack_bar.open = True
        self.page.update()

    def find_amount_field(self, section_name):
        for control in self.sections_content.controls[-1].controls:
            if isinstance(control, ft.Card) and control.content.content.controls[0].value == section_name:
                return control.content.content.controls[2].controls[0]
        return None

    def show_section_history(self, section):
        records = db.search(Query().section == section['name'])
        records.sort(key=lambda r: (r['year'], r['month'], r['day']), reverse=True)

        history_text = "\n".join([f"{r['day']}/{r['month']}/{r['year']}: ${r['amount']:.2f}" for r in records])

        alert_dialog = ft.AlertDialog(
            title=ft.Text(f"{section['name']} History"),
            content=ft.Text(history_text),
            actions=[
                ft.TextButton("Close", on_click=self.close_dialog),
            ],
        )

        self.page.dialog = alert_dialog
        alert_dialog.open = True
        self.page.update()

    def close_dialog(self, e):
        self.page.dialog.open = False
        self.page.update()

    def add_new_section(self, e):
        def save_new_section(e):
            new_section_name = new_section_input.value
            initial_balance = float(initial_balance_input.value) if initial_balance_input.value else 0
            if new_section_name and not any(section['name'] == new_section_name for section in self.sections):
                self.sections.append({'name': new_section_name, 'balance': initial_balance})
                self.save_sections()
                self.update_sections_layout()
                self.page.dialog.open = False
            self.page.update()

        new_section_input = ft.TextField(label="New Section Name")
        initial_balance_input = ft.TextField(label="Initial Balance (optional)")
        alert_dialog = ft.AlertDialog(
            title=ft.Text("Add New Section"),
            content=ft.Column([
                new_section_input,
                initial_balance_input,
                ft.ElevatedButton(text="Save", on_click=save_new_section)
            ]),
        )

        self.page.dialog = alert_dialog
        alert_dialog.open = True
        self.page.update()

    def update_sections_layout(self):
        self.sections_content.controls.pop()  # Remove the old sections layout
        self.sections_content.controls.append(self.create_sections_layout())
        self.page.update()

    def show_sections(self, e):
        self.page.clean()
        self.page.add(self.sections_content)

    def show_history(self, e):
        self.page.clean()
        self.update_history()
        self.page.add(self.history_content)
    def show_charts(self, e):
        self.page.clean()  # Clear the existing content
        self.create_chart()  # Ensure the chart is created and updated
        self.update_chart()  # Update the chart with data

        # Add the chart content
        self.page.add(self.charts_content)

        # Handle navigation and zoom buttons
        if self.chart_type == "bar_chart":
            self.navigation_container.content = self.create_week_navigation_buttons()
        else:
            self.navigation_container.content = None

        # Add the navigation container (it will be empty for line chart)
        self.page.add(self.navigation_container)

        # Update the page with the latest content
        self.page.update()


    def update_results(self, e=None):
        year = int(self.year_dropdown.value)
        month = int(self.month_dropdown.value)
        days_in_month = get_days_in_month(year, month)

        income_record = db.get((Query().type == 'income') & (Query().year == year) & (Query().month == month))
        monthly_income = income_record['amount'] if income_record else 0
        daily_income = monthly_income / days_in_month if monthly_income else 0

        expenses = db.search((Query().type == 'expense') & (Query().year == year) & (Query().month == month))
        additional_earnings = db.search((Query().type == 'additional_earning') & (Query().year == year) & (Query().month == month))

        total_expenses = sum(expense['amount'] for expense in expenses)
        total_additional_earnings = sum(earning['amount'] for earning in additional_earnings)

        balance = monthly_income + total_additional_earnings - total_expenses

        self.income_result.value = f"Monthly Income: ${monthly_income:.2f}"
        self.expense_result.value = f"Total Expenses: ${total_expenses:.2f}"
        self.additional_earning_result.value = f"Total Additional Earnings: ${total_additional_earnings:.2f}"
        self.balance_result.value = f"Current Balance: ${balance:.2f}"
        for section in self.sections:
            section_expenses = db.search((Query().type == 'expense') & (Query().section == section) & (Query().year == year) & (Query().month == month))
            section_earnings = db.search((Query().type == 'additional_earning') & (Query().section == section) & (Query().year == year) & (Query().month == month))
            section_total = sum(earning['amount'] for earning in section_earnings) - sum(expense['amount'] for expense in section_expenses)
            # Update UI with section totals (you may need to create new Text widgets for each section)

        self.update_chart()

    def create_line_chart(self):
        return ft.LineChart(
            data_series=[],
            width=600,
            height=400,
            left_axis=ft.ChartAxis(
                title=ft.Text("Amounsst ($)"),
                title_size=1,
                labels_size=1,
                labels_interval=5,
            ),
            bottom_axis=ft.ChartAxis(
                title=ft.Text("Day of Month"),
                title_size=16,
                labels_size=20,
                labels=[],
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.WHITE),
            interactive=True,
            expand=True,
        )





    def update_chart(self):
        year = int(self.year_dropdown.value)
        month = int(self.month_dropdown.value)
        days_in_month = get_days_in_month(year, month)

        # Calculate daily income
        income_record = db.get((Query().type == 'income') & (Query().year == year) & (Query().month == month))
        monthly_income = income_record['amount'] if income_record else 0
        daily_income = monthly_income / days_in_month if monthly_income else 0

        # Calculate daily expenses
        expenses = db.search((Query().type == 'expense') & (Query().year == year) & (Query().month == month))
        daily_expenses = [0] * days_in_month
        for expense in expenses:
            day = expense.get('day', 1)
            daily_expenses[day - 1] += expense['amount']

        # Calculate daily additional earnings
        additional_earnings = db.search((Query().type == 'additional_earning') & (Query().year == year) & (Query().month == month))
        daily_additional_earnings = [0] * days_in_month
        for earning in additional_earnings:
            day = earning.get('day', 1)
            daily_additional_earnings[day - 1] += earning['amount']

        # Calculate balances
        balances = [0] * days_in_month
        cumulative_difference = 0
        for day in range(days_in_month):
            daily_difference = daily_additional_earnings[day] - daily_expenses[day]
            cumulative_difference += daily_difference
            balances[day] = daily_income + cumulative_difference

        # Update the chart based on the chart type
        start_day = (self.current_week - 1) * 7 + 1
        end_day = min(self.current_week * 7, days_in_month)

        if self.chart_type == "line_chart":
            self.update_line_chart(year, month, days_in_month, daily_income, daily_expenses, daily_additional_earnings, balances)
        elif self.chart_type == "bar_chart":
            self.update_bar_chart(daily_income, daily_expenses, daily_additional_earnings, balances, start_day, end_day)

        # Update the UI elements
        self.page.update()

    def create_bar_chart(self):
        return ft.BarChart(
            bar_groups=[],
            width=1000,
            height=500,
            left_axis=ft.ChartAxis(
                title=ft.Text("Amount ($)"),
                title_size=16,
                labels_size=50,
                labels_interval=250,
            ),
            bottom_axis=ft.ChartAxis(
                title=ft.Text("Day of Month"),
                title_size=16,
                labels_size=50,
                labels=[],
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.GREY_300,
                interval=300,
            ),
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.WHITE),
            interactive=True,
            expand=True,
        )

    def update_bar_chart(self, daily_income, daily_expenses, daily_additional_earnings, balances, start_day, end_day):
        # Ensure self.chart is a BarChart object
        if not isinstance(self.chart, ft.BarChart):
            print("Warning: self.chart is not a BarChart object.")
            return

        max_value = max(
            [daily_income] + daily_expenses + daily_additional_earnings + balances
        )

        chart_max_y = max(1000, (max_value * self.zoom_level) + 250)
        self.chart.max_y = chart_max_y
        self.chart.left_axis.labels_interval = chart_max_y / 5

        rod_width = 40 / (end_day - start_day + 1) * self.zoom_level

        self.chart.bar_groups = [
            ft.BarChartGroup(
                x=day,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=daily_income * self.zoom_level,
                        width=rod_width,
                        color=ft.colors.GREEN,
                        tooltip=f"Income: ${daily_income:.2f}",
                    ),
                    ft.BarChartRod(
                        from_y=0,
                        to_y=daily_expenses[day-1] * self.zoom_level,
                        width=rod_width,
                        color=ft.colors.RED,
                        tooltip=f"Expense: ${daily_expenses[day-1]:.2f}",
                    ),
                    ft.BarChartRod(
                        from_y=0,
                        to_y=balances[day-1] * self.zoom_level,
                        width=rod_width,
                        color=ft.colors.BLUE,
                        tooltip=f"Balance: ${balances[day-1]:.2f}",
                    ),
                    ft.BarChartRod(
                        from_y=0,
                        to_y=daily_additional_earnings[day-1] * self.zoom_level,
                        width=rod_width,
                        color=ft.colors.ORANGE,
                        tooltip=f"Additional Earning: ${daily_additional_earnings[day-1]:.2f}",
                    ),
                ],
            )
            for day in range(start_day, end_day + 1)
        ]
        self.chart.bottom_axis.labels = [ft.ChartAxisLabel(value=str(day)) for day in range(start_day, end_day + 1)]

    def update_line_chart(self, year, month, days_in_month, daily_income, daily_expenses, daily_additional_earnings, balances):
        self.chart_content = ft.LineChart(
            tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.WHITE),
            expand=True,
            left_axis=ft.ChartAxis(
                title=ft.Text("Amount ($)"),
                title_size=16,
                labels_size=50,
                labels_interval=1000,
            ),
            bottom_axis=ft.ChartAxis(title=ft.Text("Day of Month")),
            top_axis=ft.ChartAxis(title=ft.Text(f"Financial Overview - {month}/{year}")),
            right_axis=ft.ChartAxis(
                title_size=16,
                labels_size=50,
                labels_interval=1000,
            ),
            data_series=[],
        )
        self.chart_with_zoom.controls = [self.chart_content]

        cumulative_income = [daily_income * (day + 1) for day in range(days_in_month)]
        cumulative_expenses = [sum(daily_expenses[:day+1]) for day in range(days_in_month)]
        cumulative_earnings = [sum(daily_additional_earnings[:day+1]) for day in range(days_in_month)]

        self.chart_content.data_series = [
            ft.LineChartData(
                color=ft.colors.GREEN,
                stroke_width=2,
                curved=True,
                data_points=[ft.LineChartDataPoint(x, y) for x, y in enumerate(cumulative_income)],
            ),
            ft.LineChartData(
                color=ft.colors.RED,
                stroke_width=2,
                curved=True,
                data_points=[ft.LineChartDataPoint(x, y) for x, y in enumerate(cumulative_expenses)],
            ),
            ft.LineChartData(
                color=ft.colors.ORANGE,
                stroke_width=2,
                curved=True,
                data_points=[ft.LineChartDataPoint(x, y) for x, y in enumerate(cumulative_earnings)],
            ),
            ft.LineChartData(
                color=ft.colors.BLUE,
                stroke_width=3,
                curved=True,
                data_points=[ft.LineChartDataPoint(x, y) for x, y in enumerate(balances)],
            ),
        ]

    def create_chart_type_dropdown(self):
        return ft.Dropdown(
            label="Select Chart Type",
            options=[
                ft.dropdown.Option("Bar Chart"),
                ft.dropdown.Option("Line Chart")
            ],
            value="Bar Chart",
            on_change=self.set_chart_type,
            width=200
        )

    def set_chart_type(self, e):
        self.chart_type = e.control.value.lower().replace(" ", "_")
        self.create_chart()  # Create the chart based on the new type
        self.update_chart()  # Update the chart with data

        # Update navigation buttons based on chart type
        if self.chart_type == "bar_chart":
            self.navigation_container.content = self.create_week_navigation_buttons()
        else:
            self.navigation_container.content = None

        self.page.update()  # Refresh the page



    def create_history_table(self):
        records = db.all()

        # Sort records based on the selected order
        if self.history_sort_order == "newest_first":
            records.sort(key=lambda r: (r.get('year', 0), r.get('month', 0), r.get('day', 0)), reverse=True)
        elif self.history_sort_order == "oldest_first":
            records.sort(key=lambda r: (r.get('year', 0), r.get('month', 0), r.get('day', 0)))
        elif self.history_sort_order == "highest_amount":
            records.sort(key=lambda r: r['amount'], reverse=True)
        elif self.history_sort_order == "lowest_amount":
            records.sort(key=lambda r: r['amount'])

        history_rows = []

        for record in records:
            record_type = record['type'].capitalize()
            amount = record['amount']
            day = record.get('day', 'N/A')
            month = record.get('month', 'N/A')
            year = record.get('year', 'N/A')

            history_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(record_type)),
                    ft.DataCell(ft.Text(f"${amount:.2f}")),
                    ft.DataCell(ft.Text(f"{day}/{month}/{year}")),
                ])
            )

        last_update = get_db_last_modified_time()

        return ft.ListView(
            controls=[
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Type")),
                        ft.DataColumn(ft.Text("Amount")),
                        ft.DataColumn(ft.Text("Date")),
                    ],
                    rows=history_rows,
                ),
                ft.Text(f"Last database update: {last_update}")
            ],
            height=500,
            spacing=10,
            padding=10,
            expand=True,
            auto_scroll=False
        )

    def update_history(self):
        self.history_list_view.controls.clear()
        self.history_list_view.controls.append(self.create_history_table())
        self.page.update()




        self.page.update()  # Refresh the page
    def zoom_in(self, e):
        self.zoom_level = min(self.zoom_level * 1.2, self.max_zoom)
        self.update_chart()
        self.page.update()

    def zoom_out(self, e):
        self.zoom_level = max(self.zoom_level / 1.2, self.min_zoom)
        self.update_chart()
        self.page.update()
    def create_week_navigation_buttons(self):
        self.navigation_buttons_row = ft.Row(
            [
                ft.IconButton(icon=ft.icons.ARROW_LEFT, on_click=self.previous_week),
                ft.IconButton(icon=ft.icons.ARROW_RIGHT, on_click=self.next_week),
                ft.IconButton(icon=ft.icons.REMOVE, on_click=self.zoom_out),
                ft.IconButton(icon=ft.icons.ADD, on_click=self.zoom_in),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )
        return self.navigation_buttons_row




    def previous_week(self, _):
        if self.current_week > 1:
            self.current_week -= 1
            self.update_chart()
            self.page.update()

    def next_week(self, _):
        year = int(self.year_dropdown.value)
        month = int(self.month_dropdown.value)
        days_in_month = get_days_in_month(year, month)
        max_weeks = (days_in_month + 6) // 7
        if self.current_week < max_weeks:
            self.current_week += 1
            self.update_chart()
            self.page.update()

    def save_income(self, e):
        try:
            income = float(self.income_input.value)
            year = int(self.year_dropdown.value)
            month = int(self.month_dropdown.value)
            db.upsert({'type': 'income', 'amount': income, 'year': year, 'month': month}, 
                    (Query().type == 'income') & (Query().year == year) & (Query().month == month))
            self.update_results()
            self.update_history()  # Update the history table
            self.page.update()
        except ValueError:
            self.income_result.value = "Please enter a valid number"
            self.page.update()





    def save_expense(self, e):
        try:
            expense = float(self.expense_input.value)
            if self.day_dropdown.value is None:
                raise ValueError("Day must be selected.")
            day = int(self.day_dropdown.value)
            year = int(self.year_dropdown.value)
            month = int(self.month_dropdown.value)
            section = self.section_dropdown.value  # Add a dropdown for selecting the section
            db.insert({'type': 'expense', 'amount': expense, 'day': day, 'year': year, 'month': month, 'section': section})
            self.update_results()
            self.update_history()
            self.page.update()
        except ValueError as ve:
            self.expense_result.value = str(ve)
            self.page.update()


    def save_additional_earning(self, e):
            try:
                earning = float(self.additional_earning_input.value)
                day = int(self.additional_earning_day_dropdown.value)
                year = int(self.year_dropdown.value)
                month = int(self.month_dropdown.value)
                section = self.section_dropdown.value  # Add a dropdown for selecting the section
                db.insert({'type': 'additional_earning', 'amount': earning, 'day': day, 'year': year, 'month': month, 'section': section})
                self.update_results()
                self.update_history()
                self.page.update()
            except ValueError:
                self.additional_earning_result.value = "Please enter a valid number"
                self.page.update()
    def create_history_table(self):
        records = db.all()

        # Sort records based on the selected order
        if self.history_sort_order == "newest_first":
            records.sort(key=lambda r: (r.get('year', 0), r.get('month', 0), r.get('day', 0)), reverse=True)
        elif self.history_sort_order == "oldest_first":
            records.sort(key=lambda r: (r.get('year', 0), r.get('month', 0), r.get('day', 0)))
        elif self.history_sort_order == "highest_amount":
            records.sort(key=lambda r: r['amount'], reverse=True)
        elif self.history_sort_order == "lowest_amount":
            records.sort(key=lambda r: r['amount'])

        history_rows = []

        for record in records:
            record_type = record['type'].capitalize()
            amount = record['amount']
            day = record.get('day', 'N/A')
            month = record.get('month', 'N/A')
            year = record.get('year', 'N/A')

            history_rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(record_type)),
                    ft.DataCell(ft.Text(f"${amount:.2f}")),
                    ft.DataCell(ft.Text(f"{day}/{month}/{year}")),
                ])
            )

        last_update = get_db_last_modified_time()

        return ft.Column([
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Type")),
                    ft.DataColumn(ft.Text("Amount")),
                    ft.DataColumn(ft.Text("Date")),
                ],
                rows=history_rows,
            ),
            ft.Text(f"Last database update: {last_update}")
        ])


    def save_expense_or_earning(self, e):
        try:
            year = int(self.year_dropdown.value)
            month = int(self.month_dropdown.value)

            if self.expense_input.value:
                expense = float(self.expense_input.value)
                if self.day_dropdown.value is None:
                    raise ValueError("Day must be selected for expense.")
                day = int(self.day_dropdown.value)
                db.insert({'type': 'expense', 'amount': expense, 'day': day, 'year': year, 'month': month})
                self.expense_input.value = ""
                self.day_dropdown.value = None

            if self.additional_earning_input.value:
                earning = float(self.additional_earning_input.value)
                if self.additional_earning_day_dropdown.value is None:
                    raise ValueError("Day must be selected for additional earning.")
                day = int(self.additional_earning_day_dropdown.value)
                db.insert({'type': 'additional_earning', 'amount': earning, 'day': day, 'year': year, 'month': month})
                self.additional_earning_input.value = ""
                self.additional_earning_day_dropdown.value = None

            self.update_results()
            self.update_history()
            self.page.update()
        except ValueError as ve:
            self.expense_result.value = str(ve)
            self.additional_earning_result.value = str(ve)
            self.page.update()

    def show_history(self, e):
        self.page.clean()
        self.update_history()
        self.page.add(self.history_content)

def main(page: ft.Page):
    ExpenseTrackerApp(page)

ft.app(target=main)
