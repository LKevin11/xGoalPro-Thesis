from PyQt5.QtCore import QObject, pyqtSignal
from threading import Thread
from PyQt5.QtWidgets import QWidget
from Model.TrainingModel import TrainingModel
from View.Training.TrainingEditView import TrainingEditView
from View.Training.TrainingLoadingView import TrainingLoadingView


class TrainingController(QObject):
    """
    Controller for the Training module.

    Manages interactions between the TrainingModel and the Training UI views
    (TrainingEditView and TrainingLoadingView). Handles starting model training
    in a separate thread, updating the loading view with log messages, and 
    emitting signals for success, errors, or navigation events.

    Signals:
        return_to_home (pyqtSignal): Emitted to navigate back to the main home screen.
        switch_to_view (pyqtSignal[QWidget]): Emitted to switch the currently displayed view.
        error_occurred (pyqtSignal[list]): Emitted when an error occurs, passing a list of error messages.
        information (pyqtSignal[list]): Emitted for general informational messages.
    
    Attributes:
        __model (TrainingModel): The training model handling SVR training.
        __edit_view (TrainingEditView): UI view for entering training parameters.
        __loading_view (TrainingLoadingView): UI view for showing training progress and logs.
    """
    return_to_home = pyqtSignal()
    switch_to_view = pyqtSignal(QWidget)
    error_occurred = pyqtSignal(list)
    information = pyqtSignal(list)

    def __init__(self, model, edit_view, loading_view):
        """
        Initialize the controller with the model and the views, 
        and setup signal-slot connections.

        Args:
            model (TrainingModel): The training model.
            edit_view (TrainingEditView): The view for training input.
            loading_view (TrainingLoadingView): The view showing training progress.
        """
        super().__init__()
        self.__model: TrainingModel = model
        self.__edit_view: TrainingEditView = edit_view
        self.__loading_view: TrainingLoadingView = loading_view
        self.__init_connections()

    def __init_connections(self) -> None:
        """
        Connect signals from the views and model to the appropriate controller slots.

        Handles starting training, navigation, and log updates.
        """
        self.__edit_view.train_button.clicked.connect(self.__start_training)
        self.__edit_view.home_button.clicked.connect(lambda: self.return_to_home.emit())
        self.__loading_view.back_button.clicked.connect(lambda: self.__on_loading_view_back_button_click())
        self.__model.log_message.connect(self.__loading_view.append_log)
        self.__model.training_finished.connect(self.__on_training_finished)

    def __start_training(self) -> None:
        """
        Start SVR training in a separate thread using parameters from the edit view.

        Disables the loading view button and switches to the loading view while training.
        """
        team = self.__edit_view.team_input.text()
        y_from = self.__edit_view.year_from.value()
        y_to = self.__edit_view.year_to.value()

        param_ranges = {
            "C_min": self.__edit_view.c_min.value(),
            "C_max": self.__edit_view.c_max.value(),
            "gamma_min": self.__edit_view.gamma_min.value(),
            "gamma_max": self.__edit_view.gamma_max.value(),
        }

        self.switch_to_view.emit(self.__loading_view)
        self.__loading_view.disable_button()
        thread = Thread(target=self.__model.train_svr, args=(team, y_from, y_to, param_ranges))
        thread.start()

    def __on_training_finished(self, success, message) -> None:
        """
        Handle completion of training.

        Emits informational or error signals based on training success, and
        re-enables the loading view button.

        Args:
            success (bool): Whether the training succeeded.
            message (str): Message describing the result of training.
        """
        if success:
            self.information.emit([message])
        else:
            self.error_occurred.emit([message])

        self.__loading_view.enable_button()

    def __on_loading_view_back_button_click(self):
        """
        Handle the back button click in the loading view.

        Clears the training log and switches back to the training edit view.
        """
        self.__loading_view.clear_log()
        self.switch_to_view.emit(self.__edit_view)
