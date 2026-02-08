using Snake.Model.Model;
using Snake.Model.Persistence;
using Snake.WPF.ViewModel;
using System.Configuration;
using System.Data;
using System.Timers;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace Snake.WPF
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {

        #region Fields

        private GameModel _model = null!;
        private SnakeViewModel _viewModel = null!;
        private MainWindow _view = null!;

        #endregion

        /// <summary>
        /// Az alkalmazás példányosítása.
        /// </summary>
        #region Constructors

        public App()
        {
            Startup += new StartupEventHandler(App_Startup);
        }

        #endregion


        #region Application event handlers

        /// <summary>
        /// Példányosítások és függőségek beállítása az app indulásakor.
        /// </summary>
        private void App_Startup(object sender, StartupEventArgs e)
        {
            // modell létrehozása
            _model = new GameModel(new TextFileManager());

            // nézetmodell létrehozása
            _viewModel = new SnakeViewModel(_model);
            _viewModel.NewGame += new EventHandler(ViewModel_LoadNewGame);
            _viewModel.StartGame += new EventHandler(ViewModel_StartGame);
            _viewModel.ViewModelGameOver += new EventHandler(ViewModel_GameOver);
            _viewModel.Quit += new EventHandler(ViewModel_Quit);

            // nézet létrehozáse
            _view = new MainWindow();
            _view.DataContext = _viewModel;
            _view.Show();


        }

        #endregion


        #region ViewModel event handlers

        /// <summary>
        /// LoadNewGame esemény eseménykezelője a modell betöltésével.
        /// </summary>
        private void ViewModel_LoadNewGame(object? sender, EventArgs e)
        {

            try
            {

                if (_viewModel.IsGameFieldSmall) { _model?.Load(GameFieldSize.SMALL); }

                if (_viewModel.IsGameFieldMedium) { _model?.Load(GameFieldSize.MEDIUM); }

                if (_viewModel.IsGameFieldLarge) { _model?.Load(GameFieldSize.LARGE); }

                _viewModel.IsStartGameButtonEnabled = true;

                _view.WelcomeOverlay.Visibility = Visibility.Collapsed;

            }
            catch(FileManagerException message)
            {
                MessageBox.Show(message.Message,
                            "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }

            

        }

        /// <summary>
        /// StartGame esemény eseménykezelője új játék kezdésével.
        /// </summary>
        private void ViewModel_StartGame(object? sender, EventArgs e)
        {

            _viewModel.IsStartGameButtonEnabled = false;
            _viewModel.IsGameOver = false;

            _viewModel.IsMenuEnabled = false;

            _model.RestartGame();


        }

        /// <summary>
        /// GameOver esemény eseménykezelője.
        /// </summary>
        private void ViewModel_GameOver(object? sender, EventArgs e)
        {

            Console.WriteLine(_model.Score);

            MessageBox.Show("Game Over\nScore: " + _model.Score,
                            "Information", MessageBoxButton.OK, MessageBoxImage.Information);


        }

        /// <summary>
        /// Exit
        /// </summary>
        private void ViewModel_Quit(object? sender, EventArgs e)
        {
            Application.Current.Shutdown();
        }

        #endregion


    }

}
