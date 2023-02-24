""" Entry point for the graphical user interface """
from PySide6.QtGui import QIcon

qss = """
QWidget {
    background: pink;
    color:rgba(228, 231, 235, 1.000);
    selection-color:rgba(228, 231, 235, 1.000);
    selection-background-color:rgba(95, 154, 244, 0.400)
}

QWidget:disabled {color:rgba(228, 231, 235, 0.400);selection-background-color:rgba(228, 231, 235, 0.200);selection-color:rgba(228, 231, 235, 0.400)}
QWidget:focus {outline:none}
QCheckBox:!window,QRadioButton:!window,QPushButton:!window,QLabel:!window,QLCDNumber:!window {background:transparent}
QMdiSubWindow > QCheckBox:!window,QMdiSubWindow > QRadioButton:!window,QMdiSubWindow > QPushButton:!window,QMdiSubWindow > QLabel:!window,QMdiSubWindow > QLCDNumber:!window {background:rgba(32, 33, 36, 1.000)}QMainWindow::separator {width:4px;height:4px;background:rgba(63, 64, 66, 1.000)}QMainWindow::separator:hover,QMainWindow::separator:pressed {background:rgba(138, 180, 247, 1.000)}QToolTip {background:rgba(42, 43, 47, 1.000);color:rgba(228, 231, 235, 1.000)}QSizeGrip {width:0;height:0;image:none}QStatusBar {background:rgba(42, 43, 46, 1.000)}QStatusBar::item {border:none}QStatusBar QWidget {background:transparent;padding:3px;border-radius:4px}QStatusBar > .QSizeGrip {padding:0}QStatusBar QWidget:hover {background:rgba(255, 255, 255, 0.133)}QStatusBar QWidget:pressed,QStatusBar QWidget:checked {background:rgba(255, 255, 255, 0.204)}QCheckBox,QRadioButton {border-top:2px solid transparent;border-bottom:2px solid transparent}QCheckBox:hover,QRadioButton:hover {border-bottom:2px solid rgba(138, 180, 247, 1.000)}QGroupBox {font-weight:bold;margin-top:8px;padding:2px 1px 1px 1px;border-radius:4px;border:1px solid rgba(63, 64, 66, 1.000)}QGroupBox::title {subcontrol-origin:margin;subcontrol-position:top left;left:7px;margin:0 2px 0 3px}QGroupBox:flat {border-color:transparent}QMenuBar {padding:2px;border-bottom:1px solid rgba(63, 64, 66, 1.000);background:rgba(32, 33, 36, 1.000)}QMenuBar::item {background:transparent;padding:4px}QMenuBar::item:selected {padding:4px;border-radius:4px;background:rgba(255, 255, 255, 0.145)}QMenuBar::item:pressed {padding:4px;margin-bottom:0;padding-bottom:0}QToolBar {padding:1px;font-weight:bold;spacing:2px;margin:1px;background:rgba(51, 51, 51, 1.000);border-style:none}QToolBar::handle:horizontal {width:20px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/drag_indicator_e1e5e9_0.svg)}QToolBar::handle:vertical {height:20px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/drag_indicator_e1e5e9_90.svg)}QToolBar::handle:horizontal:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/drag_indicator_e4e7eb66_0.svg)}QToolBar::handle:vertical:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/drag_indicator_e4e7eb66_90.svg)}QToolBar::separator {background:rgba(63, 64, 66, 1.000)}QToolBar::separator:horizontal {width:2px;margin:0 6px}QToolBar::separator:vertical {height:2px;margin:6px 0}QToolBar > QToolButton {background:transparent;padding:3px;border-radius:4px}QToolBar > QToolButton:hover,QToolBar > QToolButton::menu-button:hover {background:rgba(255, 255, 255, 0.133)}QToolBar > QToolButton::menu-button {border-top-right-radius:4px;border-bottom-right-radius:4px}QToolBar > QToolButton:pressed,QToolBar > QToolButton::menu-button:pressed:enabled,QToolBar > QToolButton:checked:enabled {background:rgba(255, 255, 255, 0.204)}QToolBar > QWidget {background:transparent}QMenu {background:rgba(42, 43, 47, 1.000);padding:8px 0; border-radius:4px;}QMenu::separator {margin:4px 0;height:1px;background:rgba(63, 64, 66, 1.000)}QMenu::item {padding:4px 19px}QMenu::item:selected {background:rgba(255, 255, 255, 0.133)}QMenu::icon {padding-left:10px;width:14px;height:14px}QMenu::right-arrow {margin:2px;padding-left:12px;height:20px;width:20px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e1e5e9_0.svg)}QMenu::right-arrow:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e4e7eb66_0.svg)}QScrollBar {background:rgba(255, 255, 255, 0.063);border-radius:4px;background:transparent}QScrollBar:horizontal {height:14px;height:7px;}QScrollBar:vertical {width:14px;width:7px;}QScrollBar::handle {background:rgba(255, 255, 255, 0.188);border-radius:3px}QScrollBar::handle:hover {background:rgba(255, 255, 255, 0.271)}QScrollBar::handle:pressed {background:rgba(255, 255, 255, 0.376)}QScrollBar::handle:disabled {background:rgba(255, 255, 255, 0.082)}QScrollBar::handle:horizontal {min-width:8px;margin:4px 14px;margin:0;}QScrollBar::handle:horizontal:hover {margin:2px 14px;margin:0;}QScrollBar::handle:vertical {min-height:8px;margin:14px 4px;margin:0;}QScrollBar::handle:vertical:hover {margin:14px 2px;margin:0;}QScrollBar::sub-page,QScrollBar::add-page {background:transparent}QScrollBar::sub-line,QScrollBar::add-line {background:transparent;width:0;height:0}QScrollBar::up-arrow:enabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff2f_0.svg)}QScrollBar::right-arrow:enabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff2f_90.svg)}QScrollBar::down-arrow:enabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff2f_180.svg)}QScrollBar::left-arrow:enabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff2f_270.svg)}QScrollBar::up-arrow:hover {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff5f_0.svg)}QScrollBar::right-arrow:hover {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff5f_90.svg)}QScrollBar::down-arrow:hover {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff5f_180.svg)}QScrollBar::left-arrow:hover {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_ffffff5f_270.svg)}QProgressBar {text-align:center;border:1px solid rgba(63, 64, 66, 1.000);border-radius:4px}QProgressBar::chunk {background:rgba(102, 159, 245, 1.000);border-radius:3px}QProgressBar::chunk:disabled {background:rgba(228, 231, 235, 0.200)}QPushButton {color:rgba(138, 180, 247, 1.000);border:1px solid rgba(63, 64, 66, 1.000);padding:4px 8px;border-radius:4px}QPushButton:flat,QPushButton:default {border:none;padding:5px 9px}QPushButton:default {color:rgba(32, 33, 36, 1.000);background:rgba(138, 180, 247, 1.000)}QPushButton:hover {background:rgba(102, 159, 245, 0.110)}QPushButton:pressed {background:rgba(87, 150, 244, 0.230)}QPushButton:checked:enabled {background:rgba(87, 150, 244, 0.230)}QPushButton:default:hover {background:rgba(117, 168, 246, 1.000)}QPushButton:default:pressed,QPushButton:default:checked {background:rgba(95, 154, 244, 1.000)}QPushButton:default:disabled,QPushButton:default:checked:disabled {background:rgba(228, 231, 235, 0.200)}QDialogButtonBox {dialogbuttonbox-buttons-have-icons:0}QDialogButtonBox QPushButton {min-width:65px}QToolButton {background:transparent;padding:5px;spacing:2px;border-radius:2px}QToolButton:hover,QToolButton::menu-button:hover {background:rgba(102, 159, 245, 0.110)}QToolButton:pressed,QToolButton:checked:pressed,QToolButton::menu-button:pressed:enabled {background:rgba(87, 150, 244, 0.230)}QToolButton:selected:enabled,QToolButton:checked:enabled {background:rgba(87, 150, 244, 0.230)}QToolButton::menu-indicator {height:18px;width:18px;top:6px;left:3px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e1e5e9_180.svg)}QToolButton::menu-indicator:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e4e7eb66_180.svg)}QToolButton::menu-arrow {image:unset}QToolButton::menu-button {subcontrol-origin:margin;width:17px;border-top-right-radius:2px;border-bottom-right-radius:2px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e1e5e9_180.svg)}QToolButton::menu-button:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e4e7eb66_180.svg)}QToolButton[popupMode=MenuButtonPopup] {padding-right:1px;margin-right:18px;border-top-right-radius:0;border-bottom-right-radius:0}QComboBox {min-height:1.5em;padding:0 8px 0 4px;background:rgba(63, 64, 66, 1.000);border:1px solid rgba(63, 64, 66, 1.000);border-radius:4px}QComboBox:focus,QComboBox:open {border-color:rgba(138, 180, 247, 1.000)}QComboBox::drop-down {margin:2px 2px 2px -6px;border-radius:4}QComboBox::drop-down:editable:hover {background:rgba(255, 255, 255, 0.145)}QComboBox::down-arrow {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e1e5e9_180.svg)}QComboBox::down-arrow:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e4e7eb66_180.svg)}QComboBox::down-arrow:editable:open {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e1e5e9_0.svg)}QComboBox::down-arrow:editable:open:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e4e7eb66_0.svg)}QComboBox::item:selected {border:none;background:rgba(66, 136, 242, 0.400);border-radius:4px}QComboBox QListView[frameShape=NoFrame] {margin:0;padding:4px;background:rgba(42, 43, 47, 1.000); border-radius:0; border-radius:4px;}QComboBox QListView::item {border-radius:4px}QSlider {padding:2px 0}QSlider::groove {border-radius:2px}QSlider::groove:horizontal {height:4px}QSlider::groove:vertical {width:4px}QSlider::sub-page:horizontal,QSlider::add-page:vertical,QSlider::handle {background:rgba(138, 180, 247, 1.000)}QSlider::sub-page:horizontal:disabled,QSlider::add-page:vertical:disabled,QSlider::handle:disabled {background:rgba(228, 231, 235, 0.200)}QSlider::add-page:horizontal,QSlider::sub-page:vertical {background:rgba(228, 231, 235, 0.100)}QSlider::handle:hover,QSlider::handle:pressed {background:rgba(106, 161, 245, 1.000)}QSlider::handle:horizontal {width:16px;height:8px;margin:-6px 0;border-radius:8px}QSlider::handle:vertical {width:8px;height:16px;margin:0 -6px;border-radius:8px}QTabWidget::pane {border:1px solid rgba(63, 64, 66, 1.000);border-radius:4px}QTabBar {qproperty-drawBase:0}QTabBar::close-button {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/close_e1e5e9_0.svg)}QTabBar::close-button:hover {background:rgba(255, 255, 255, 0.145);border-radius:4px}QTabBar::close-button:!selected {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/close_e4e7eb99_0.svg)}QTabBar::close-button:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/close_e4e7eb66_0.svg)}QTabBar::tab {padding:3px;border-style:solid}QTabBar::tab:hover,QTabBar::tab:selected:hover:enabled {background:rgba(255, 255, 255, 0.094)}QTabBar::tab:selected:enabled {color:rgba(138, 180, 247, 1.000);background:rgba(255, 255, 255, 0.000);border-color:rgba(138, 180, 247, 1.000)}QTabBar::tab:selected:disabled,QTabBar::tab:only-one:selected:enabled {border-color:rgba(63, 64, 66, 1.000)}QTabBar::tab:top {border-bottom-width:2px;margin:3px 6px 0 0;border-top-left-radius:2px;border-top-right-radius:2px}QTabBar::tab:bottom {border-top-width:2px;margin:0 6px 3px 0;border-bottom-left-radius:2px;border-bottom-right-radius:2px}QTabBar::tab:left {border-right-width:2px;margin:0 0 6px 3px;border-top-left-radius:2px;border-bottom-left-radius:2px}QTabBar::tab:right {border-left-width:2px;margin-bottom:6px;margin:0 3px 6px 0;border-top-right-radius:2px;border-bottom-right-radius:2px}QTabBar::tab:top:first,QTabBar::tab:top:only-one,QTabBar::tab:bottom:first,QTabBar::tab:bottom:only-one {margin-left:2px}QTabBar::tab:top:last,QTabBar::tab:top:only-one,QTabBar::tab:bottom:last,QTabBar::tab:bottom:only-one {margin-right:2px}QTabBar::tab:left:first,QTabBar::tab:left:only-one,QTabBar::tab:right:first,QTabBar::tab:right:only-one {margin-top:2px}QTabBar::tab:left:last,QTabBar::tab:left:only-one,QTabBar::tab:right:last,QTabBar::tab:right:only-one {margin-bottom:2px}QDockWidget {border:1px solid rgba(63, 64, 66, 1.000);border-radius:4px}QDockWidget::title {padding:3px;spacing:4px;background:rgba(22, 23, 25, 1.000)}QDockWidget::close-button,QDockWidget::float-button {border-radius:2px}QDockWidget::close-button:hover,QDockWidget::float-button:hover {background:rgba(102, 159, 245, 0.110)}QDockWidget::close-button:pressed,QDockWidget::float-button:pressed {background:rgba(87, 150, 244, 0.230)}QFrame {border:1px solid rgba(63, 64, 66, 1.000);padding:1px;border-radius:4px}.QFrame {padding:0}QFrame[frameShape=NoFrame] {border-color:transparent;padding:0}.QFrame[frameShape=NoFrame] {border:none}QFrame[frameShape=Panel] {border-color:rgba(22, 23, 25, 1.000);background:rgba(22, 23, 25, 1.000)}QFrame[frameShape=HLine] {max-height:2px;border:none;background:rgba(63, 64, 66, 1.000)}QFrame[frameShape=VLine] {max-width:2px;border:none;background:rgba(63, 64, 66, 1.000)}QLCDNumber {min-width:2em;margin:2px}QToolBox::tab {background:rgba(22, 23, 25, 1.000);border-bottom:2px solid rgba(63, 64, 66, 1.000);border-top-left-radius:4px;border-top-right-radius:4px}QToolBox::tab:selected:enabled {border-bottom-color:rgba(138, 180, 247, 1.000)}QSplitter::handle {background:rgba(63, 64, 66, 1.000);margin:1px 3px}QSplitter::handle:hover {background:rgba(138, 180, 247, 1.000)}QSplitter::handle:horizontal {width:5px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/horizontal_rule_e1e5e9_90.svg)}QSplitter::handle:horizontal:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/horizontal_rule_e4e7eb66_90.svg)}QSplitter::handle:vertical {height:5px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/horizontal_rule_e1e5e9_0.svg)}QSplitter::handle:vertical:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/horizontal_rule_e4e7eb66_0.svg)}QSplitterHandle::item:hover {}QAbstractScrollArea {margin:1px}QAbstractScrollArea::corner {background:transparent}QAbstractScrollArea > .QWidget {background:transparent}QAbstractScrollArea > .QWidget > .QWidget {background:transparent}QMdiArea {qproperty-background:rgba(22, 23, 25, 1.000);border-radius:0}QMdiSubWindow {background:rgba(32, 33, 36, 1.000);border:1px solid;padding:0 3px}QMdiSubWindow > QWidget {border:1px solid rgba(63, 64, 66, 1.000)}QTextEdit, QPlainTextEdit {background:rgba(28, 29, 31, 1.000)}QTextEdit:focus,QTextEdit:selected,QPlainTextEdit:focus,QPlainTextEdit:selected {border:1px solid rgba(138, 180, 247, 1.000);selection-background-color:rgba(95, 154, 244, 0.400)}QTextEdit:!focus,QPlainTextEdit:!focus { selection-background-color:rgba(255, 255, 255, 0.125)}QTextEdit:!active,QPlainTextEdit:!active { }QAbstractItemView {padding:0;alternate-background-color:transparent;selection-background-color:transparent}QAbstractItemView:disabled {selection-background-color:transparent}QAbstractItemView::item:alternate,QAbstractItemView::branch:alternate {background:rgba(255, 255, 255, 0.047)}QAbstractItemView::item:selected,QAbstractItemView::branch:selected {background:rgba(66, 136, 242, 0.400)}QAbstractItemView::item:selected:!active,QAbstractItemView::branch:selected:!active {background:rgba(210, 227, 252, 0.150)}QAbstractItemView QLineEdit,QAbstractItemView QAbstractSpinBox,QAbstractItemView QAbstractButton {padding:0;margin:1px}QListView {padding:1px}QListView,QTreeView {background:rgba(32, 33, 36, 1.000)}QListView::item:!selected:hover,QTreeView::item:!selected:hover,QTreeView::branch:!selected:hover {background:rgba(255, 255, 255, 0.075)}QTreeView::branch:!selected:hover,QTreeView::branch:alternate,QTreeView::branch:selected,QTreeView::branch:selected:!active { background:transparent;}QTreeView::branch {border-image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/vertical_line_ffffff35_0.svg) 0}QTreeView::branch:active {border-image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/vertical_line_ffffff5f_0.svg) 0}QTreeView::branch:has-siblings:adjoins-item,QTreeView::branch:!has-children:!has-siblings:adjoins-item {border-image:unset}QTreeView::branch:has-children:!has-siblings:closed,QTreeView::branch:closed:has-children:has-siblings {border-image:unset;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e1e5e9_0.svg)}QTreeView::branch:has-children:!has-siblings:closed:disabled,QTreeView::branch:closed:has-children:has-siblings:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e4e7eb66_0.svg)}QTreeView::branch:open:has-children:!has-siblings,QTreeView::branch:open:has-children:has-siblings {border-image:unset;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e1e5e9_180.svg)}QTreeView::branch:open:has-children:!has-siblings:disabled,QTreeView::branch:open:has-children:has-siblings:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e4e7eb66_180.svg)}QTreeView > QHeaderView {background:rgba(32, 33, 36, 1.000)}QTreeView > QHeaderView::section {background:rgba(63, 64, 66, 1.000)}QListView::left-arrow {margin:-2px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e4e7eb99_180.svg)}QListView::right-arrow {margin:-2px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e4e7eb99_0.svg)}QListView::left-arrow:selected:enabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e1e5e9_180.svg)}QListView::right-arrow:selected:enabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e1e5e9_0.svg)}QListView::left-arrow:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e4e7eb66_180.svg)}QListView::right-arrow:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/chevron_right_e4e7eb66_0.svg)}QColumnView {background:rgba(32, 33, 36, 1.000)}QColumnViewGrip {margin:-4px;background:rgba(32, 33, 36, 1.000);image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/drag_handle_e1e5e9_90.svg)}QColumnViewGrip:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/drag_handle_e4e7eb66_90.svg)}QTableView {gridline-color:rgba(63, 64, 66, 1.000);background:rgba(16, 16, 18, 1.000);selection-background-color:rgba(66, 136, 242, 0.550); alternate-background-color:rgba(255, 255, 255, 0.082);}QTableView:!active { }QTableView::item:alternate { }QTableView::item:selected { }QTableView QTableCornerButton::section {margin:0 1px 1px 0;background:rgba(63, 64, 66, 1.000);border-top-left-radius:2px}QTableView QTableCornerButton::section:pressed {background:rgba(66, 136, 242, 0.550)}QTableView > QHeaderView {background:rgba(16, 16, 18, 1.000);border-radius:3}QTableView > QHeaderView::section {background:rgba(63, 64, 66, 1.000)}QHeaderView {margin:0;border:none}QHeaderView::section {border:none;background:rgba(63, 64, 66, 1.000);padding-left:4px}QHeaderView::section:horizontal {margin-right:1px}QHeaderView::section:vertical {margin-bottom:1px}QHeaderView::section:on:enabled,QHeaderView::section:on:pressed {color:rgba(138, 180, 247, 1.000)}QHeaderView::section:last,QHeaderView::section:only-one {margin:0}QHeaderView::down-arrow:horizontal {margin-left:-19px;subcontrol-position:center right;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e1e5e9_180.svg)}QHeaderView::down-arrow:horizontal:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e4e7eb66_180.svg)}QHeaderView::up-arrow:horizontal {margin-left:-19px;subcontrol-position:center right;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e1e5e9_0.svg)}QHeaderView::up-arrow:horizontal:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/expand_less_e4e7eb66_0.svg)}QHeaderView::down-arrow:vertical,QHeaderView::up-arrow:vertical {width:0;height:0}QCalendarWidget > .QWidget {background:rgba(16, 16, 18, 1.000);border-bottom:1px solid rgba(63, 64, 66, 1.000);border-top-left-radius:4px;border-top-right-radius:4px}QCalendarWidget > .QWidget > QWidget {padding:1px}QCalendarWidget .QWidget > QToolButton {border-radius:4px}QCalendarWidget > QTableView {margin:0;border:none;border-radius:4px;border-top-left-radius:0;border-top-right-radius:0;alternate-background-color:rgba(255, 255, 255, 0.082); }QLineEdit,QAbstractSpinBox {padding:3px 4px;min-height:1em;border:1px solid rgba(63, 64, 66, 1.000);background:rgba(63, 64, 66, 1.000);border-radius:4px}QLineEdit:focus,QAbstractSpinBox:focus {border-color:rgba(138, 180, 247, 1.000)}QAbstractSpinBox::up-button,QAbstractSpinBox::down-button {subcontrol-position:center right;border-radius:4px}QAbstractSpinBox::up-button:hover:on,QAbstractSpinBox::down-button:hover:on {background:rgba(255, 255, 255, 0.145)}QAbstractSpinBox::up-button {bottom:5px;right:4px}QAbstractSpinBox::up-arrow:on {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_e1e5e9_0.svg)}QAbstractSpinBox::up-arrow:disabled,QAbstractSpinBox::up-arrow:off {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_e4e7eb66_0.svg)}QAbstractSpinBox::down-button {top:5px;right:4px}QAbstractSpinBox::down-arrow:on {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_e1e5e9_180.svg)}QAbstractSpinBox::down-arrow:disabled,QAbstractSpinBox::down-arrow:off {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/arrow_drop_up_e4e7eb66_180.svg)}QDateTimeEdit::drop-down {padding-right:4px;width:16px;image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/calendar_today_e1e5e9_0.svg)}QDateTimeEdit::drop-down:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/calendar_today_e4e7eb66_0.svg)}QDateTimeEdit::down-arrow[calendarPopup=true] {image:none}QFileDialog QFrame {border:none}QFontDialog QListView {min-height:60px}QComboBox::indicator,QMenu::indicator {width:18px;height:18px}QMenu::indicator {background:rgba(255, 255, 255, 0.098);margin-left:3px;border-radius:4px}QComboBox::indicator:checked,QMenu::indicator:checked {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/check_e1e5e9_0.svg)}QCheckBox,QRadioButton {spacing:8px}QGroupBox::title,QAbstractItemView::item {spacing:6px}QCheckBox::indicator,QGroupBox::indicator,QAbstractItemView::indicator,QRadioButton::indicator {height:18px;width:18px}QCheckBox::indicator,QGroupBox::indicator,QAbstractItemView::indicator {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/check_box_outline_blank_e1e5e9_0.svg)}QCheckBox::indicator:unchecked:disabled,QGroupBox::indicator:unchecked:disabled,QAbstractItemView::indicator:unchecked:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/check_box_outline_blank_e4e7eb66_0.svg)}QCheckBox::indicator:checked,QGroupBox::indicator:checked,QAbstractItemView::indicator:checked {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/check_box_8ab4f7_0.svg)}QCheckBox::indicator:checked:disabled,QGroupBox::indicator:checked:disabled,QAbstractItemView::indicator:checked:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/check_box_e4e7eb66_0.svg)}QCheckBox::indicator:indeterminate,QAbstractItemView::indicator:indeterminate {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/indeterminate_check_box_8ab4f7_0.svg)}QCheckBox::indicator:indeterminate:disabled,QAbstractItemView::indicator:indeterminate:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/indeterminate_check_box_e4e7eb66_0.svg)}QRadioButton::indicator:unchecked {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/radio_button_unchecked_e1e5e9_0.svg)}QRadioButton::indicator:unchecked:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/radio_button_unchecked_e4e7eb66_0.svg)}QRadioButton::indicator:checked {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/radio_button_checked_8ab4f7_0.svg)}QRadioButton::indicator:checked:disabled {image:url(/Users/tors10/.cache/qdarktheme/v2.1.0/radio_button_checked_e4e7eb66_0.svg)}PlotWidget {padding:0}ParameterTree > .QWidget > .QWidget > .QWidget > QComboBox{min-height:1.2em}ParameterTree::item,ParameterTree > .QWidget {background:rgba(32, 33, 36, 1.000)}
"""

if __name__ == '__main__':

    # from PySide6.QtWidgets import QApplication, QWidget
    #
    # # Only needed for access to command line arguments
    # import sys
    #
    # # You need one (and only one) QApplication instance per application.
    # # Pass in sys.argv to allow command line arguments for your app.
    # # If you know you won't use command line arguments QApplication([]) works too.
    # app = QApplication(sys.argv)
    #
    # # Create a Qt widget, which will be our window.
    # window = QWidget()
    # window.show()  # IMPORTANT!!!!! Windows are hidden by default.
    #
    # # Start the event loop.
    # app.exec_()

    # import sys
    # from PySide6.QtWidgets import QApplication, QPushButton, QStyleFactory
    # from PySide6.QtWebEngineWidgets import QWebEngineView
    # from PySide6 import QUrl
    #
    # app = QApplication(sys.argv)
    #
    # # QApplication::setStyle(QStyleFactory::create("Fusion"));
    #
    # # ("Windows", "WindowsXP", "WindowsVista", "Fusion")
    # app.setStyle(QStyleFactory.create('Fusion'))
    #
    # view = QWebEngineView()
    # view.load(QUrl("http://qt-project.org/"))
    # view.show()
    #
    # # window = QPushButton("Push Me")
    # # window.show()
    #
    # app.exec_()

    ############################

    import os
    import sys
    import ctypes
    import platform

    import qdarktheme

    # os.environ['QT_PLUGIN_PATH'] = r'E:\mambaforge\envs\pyside6\Library\lib\qt6\plugins'

    from PySide6 import QtCore
    from PySide6.QtWidgets import QApplication, QStyleFactory
    from fmpy.gui.MainWindow import MainWindow

    if os.name == 'nt' and int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    # sys.argv += ['-platform', 'windows:darkmode=2']

    app = QApplication(sys.argv)

    # app.setStyleSheet(qss)

    app.setStyleSheet("""
QWidget#startPage, QWidget#settingsPage, QWidget#dockWidgetContents, QStatusBar {
	background: white;
}    
    """)

    # minimal index.theme example in Python
    # https://stackoverflow.com/questions/74432913/switch-gui-icon-from-light-to-dark-theme-with-pyqt5

    # minimal theme example in C++
    # https://github.com/DougBeney/Qt5-Icon-Themes-Example

    # dark theme for PySide
    # https://github.com/5yutan5/PyQtDarkTheme

    # QIcon.setThemeSearchPaths([':icons'])
    # QIcon.setFallbackSearchPaths(QIcon.fallbackSearchPaths() + [":icons/light"])
    # QIcon.setThemeName('light')
    # icon = QIcon.fromTheme("book")
    # qdarktheme.setup_theme()


    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)

    print(QStyleFactory.keys())

    # app.setStyle(QStyleFactory.create('WindowsVista'))
    # app.setStyle('Fusion')

#     app.setStyleSheet("""
# QTreeView2 {
#     color: black;
#     background: #fff;
# }
#
# QTreeView {
#     background: #fff;
# }
#
# QToolBar {
#     background: #ffffff;
#     border: none;
# }
# """
#                       )

    window = MainWindow()
    window.show()

    for i, v in enumerate(sys.argv[1:]):
        if i > 0:
            window = MainWindow()
            window.show()
        window.load(v)

    sys.exit(app.exec_())
