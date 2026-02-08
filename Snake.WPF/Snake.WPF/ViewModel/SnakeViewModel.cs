using Snake.Model.Model;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Windows.Media;

namespace Snake.WPF.ViewModel
{
    public class SnakeViewModel : ViewModelBase
    {

        #region Fields

        private GameModel _snakeModel; //modell
        private bool _isStartGameButtonEnabled;
        private bool _isMenuEnabled;

        #endregion


        #region Public Properties

        /// <summary>
        /// Új játék betöltése parancs.
        /// </summary>
        public DelegateCommand NewGameCommand { get; private set; }

        /// <summary>
        /// Játék elindítása parancs.
        /// </summary>
        public DelegateCommand StartGameCommand { get; private set; }

        /// <summary>
        /// Irányváltás parancsa.
        /// </summary>
        public DelegateCommand DirectionChange { get; private set; }

        /// <summary>
        /// Szünet parancsa.
        /// </summary>
        public DelegateCommand PauseCommand { get; private set; }

        /// <summary>
        /// Exit parancs
        /// </summary>
        public DelegateCommand QuitCommand { get; private set; }

        /// <summary>
        /// Elfogyasztott tojások számának lekérdezése.
        /// </summary>
        public int Score
        {
            get
            {
                return _snakeModel.Score;
            }

            set
            {
                _snakeModel.Score = value;
                OnPropertyChanged(nameof(Score));
            }
        }

        /// <summary>
        /// Vége-e a játéknak.
        /// </summary>
        public bool IsGameOver { get { return _snakeModel.IsGameOver; } set { _snakeModel.IsGameOver = value; OnPropertyChanged(nameof(IsGameOver)); } }

        /// <summary>
        /// Kicsi pályá lekérdezése.
        /// </summary>
        public bool IsGameFieldSmall
        {
            get { return _snakeModel.Size == GameFieldSize.SMALL; }
            set
            {
                if (_snakeModel.Size == GameFieldSize.SMALL)
                    return;

                _snakeModel.Size = GameFieldSize.SMALL;
                OnPropertyChanged(nameof(IsGameFieldSmall));
                OnPropertyChanged(nameof(IsGameFieldMedium));
                OnPropertyChanged(nameof(IsGameFieldLarge));
            }
        }

        /// <summary>
        /// Közepes pálya lekérdezése.
        /// </summary>
        public bool IsGameFieldMedium
        {
            get { return _snakeModel.Size == GameFieldSize.MEDIUM; }
            set
            {
                if (_snakeModel.Size == GameFieldSize.MEDIUM)
                    return;

                _snakeModel.Size = GameFieldSize.MEDIUM;
                OnPropertyChanged(nameof(IsGameFieldSmall));
                OnPropertyChanged(nameof(IsGameFieldMedium));
                OnPropertyChanged(nameof(IsGameFieldLarge));
            }
        }

        /// <summary>
        /// Nagy pálya lekérdezése.
        /// </summary>
        public bool IsGameFieldLarge
        {
            get { return _snakeModel.Size == GameFieldSize.LARGE; }
            set
            {
                if (_snakeModel.Size == GameFieldSize.LARGE)
                    return;

                _snakeModel.Size = GameFieldSize.LARGE;
                OnPropertyChanged(nameof(IsGameFieldSmall));
                OnPropertyChanged(nameof(IsGameFieldMedium));
                OnPropertyChanged(nameof(IsGameFieldLarge));
            }
        }

        /// <summary>
        /// Startgomb elérhető-e
        /// </summary>
        public bool IsStartGameButtonEnabled
        {
            get { return _isStartGameButtonEnabled; }

            set { _isStartGameButtonEnabled = value; OnPropertyChanged(nameof(IsStartGameButtonEnabled)); }
        }

        /// <summary>
        /// Menü elérhető-e
        /// </summary>
        public bool IsMenuEnabled
        {
            get { return _isMenuEnabled; }

            set { _isMenuEnabled = value; OnPropertyChanged(nameof(IsMenuEnabled)); }
        }

        /// <summary>
        /// Pálya mérete
        /// </summary>
        public int Size
        {
            get { return _snakeModel.Rows; }
        }

        /// <summary>
        /// Dinamikus mezők tárolója
        /// </summary>
        public ObservableCollection<DynamicField> Fields { get; set; }

        #endregion


        #region Events

        /// <summary>
        /// Új játék betöltése esemény.
        /// </summary>
        public event EventHandler? NewGame;

        /// <summary>
        /// Játék elindítása esemény.
        /// </summary>
        public event EventHandler? StartGame;

        /// <summary>
        /// Gameover esemény a viewmodellben
        /// </summary>
        public event EventHandler? ViewModelGameOver;

        /// <summary>
        /// Exit esemény
        /// </summary>
        public event EventHandler? Quit;

        #endregion


        #region Constructors

        /// <summary>
        /// Snake nézetmodell példányosítása.
        /// </summary>
        /// <param name="model">A modell típusa</param>
        public SnakeViewModel(GameModel model)
        {
            //játék csatlakoztatása
            _snakeModel = model;
            _snakeModel.Eating += new EventHandler(Model_Eating);
            _snakeModel.GameLoopChanged += new EventHandler<GameLoopEventArgs>(Model_GameTimerLoopEvent);
            _snakeModel.GameOver += new EventHandler(Model_GameOver);
            _snakeModel.GameLoaded += new EventHandler(Model_GameLoaded);
            _snakeModel.RefreshEvent += new EventHandler(RefreshFields);

            //parancsok kezelése
            NewGameCommand = new DelegateCommand(param => OnNewGame());
            StartGameCommand = new DelegateCommand(param => OnStartGame());
            DirectionChange = new DelegateCommand(param => ChangeDirection(param?.ToString() ?? String.Empty));
            PauseCommand = new DelegateCommand(param => Pause());
            QuitCommand = new DelegateCommand(param => OnQuit());

            _snakeModel.IsGameOver = true;

            Fields = new ObservableCollection<DynamicField>();

            _isMenuEnabled = true;
            _isStartGameButtonEnabled = false;
        }

        #endregion


        #region Private Methods

        /// <summary>
        /// Irányváltás metóduse.
        /// </summary>
        /// <param name="d">Irány szövegesen</param>
        private void ChangeDirection(string? d)
        {

            if (_snakeModel.IsGameOver)
            {
                return;
            }

            switch (d)
            {

                case "left":
                    _snakeModel.ChangeDirection(Direction.Left); break;
                case "right":
                    _snakeModel.ChangeDirection(Direction.Right); break;
                case "up":
                    _snakeModel.ChangeDirection(Direction.Up); break;
                case "down":
                    _snakeModel.ChangeDirection(Direction.Down); break;

            }

        }

        /// <summary>
        /// Tojás elfogyasztásának jelzése
        /// </summary>
        private void Model_Eating(object? sender, EventArgs e)
        {
            OnPropertyChanged(nameof(Score));
        }

        /// <summary>
        /// Játék betöltött eseménykezelője
        /// </summary>
        private void Model_GameLoaded(object? sender, EventArgs e)
        {

            Fields.Clear();

            for(int r = 0; r < _snakeModel.Rows; r++)
            {
                for(int c = 0; c < _snakeModel.Cols; c++)
                {

                    Fields.Add(new DynamicField(r, c, 0));

                }
            }

            OnPropertyChanged(nameof(Fields));
            OnPropertyChanged(nameof(Size));
            ModifyFields();

        }

        /// <summary>
        /// Játékmező frissitése eseménykezelő
        /// </summary>
        private void RefreshFields(object? sender, EventArgs e)
        {

            ModifyFields();

        }

        /// <summary>
        /// Dinamikus mezők változtatása
        /// </summary>
        private void ModifyFields()
        {

            for (int r = 0; r < _snakeModel.Rows; ++r)
            {

                for (int c = 0; c < _snakeModel.Cols; ++c)
                {

                    if (_snakeModel!.Grid![r, c] == GridValue.Empty)
                    {
                        Fields[_snakeModel.Rows * r + c].Value = 0;
                    }
                    else if (_snakeModel.Grid[r, c] == GridValue.Snake)
                    {
                        Fields[_snakeModel.Rows * r + c].Value = 1;
                    }
                    else if (_snakeModel.Grid[r, c] == GridValue.Food)
                    {
                        Fields[_snakeModel.Rows * r + c].Value = 2;
                    }
                    else if (_snakeModel.Grid[r, c] == GridValue.Outside)
                    {
                        Fields[_snakeModel.Rows * r + c ].Value = 3;
                    }

                }

            }

            OnPropertyChanged(nameof(Fields));

        }

        /// <summary>
        /// Szünet.
        /// </summary>
        private void Pause()
        {

            if (_snakeModel.IsGameOver) return;

            _snakeModel.ManagePause();

        }

        /// <summary>
        /// Időzítő változásának eseménykezelője.
        /// </summary>
        private void Model_GameTimerLoopEvent(object? sender, GameLoopEventArgs e)
        {

            if (!e.IsRunning)
            {
                //IsStartGameButtonEnabled = true;
                IsMenuEnabled = true;
            }
            else
            {
                IsStartGameButtonEnabled = false;
                IsMenuEnabled = false;
            }

        }

        /// <summary>
        /// Model gameover eseménykezelője
        /// </summary>
        private void Model_GameOver(object? sender, EventArgs e)
        {

            IsMenuEnabled = true;
            IsStartGameButtonEnabled = true;
            OnViewModelGameOver();

        }

        #endregion


        #region Event Methods

        /// <summary>
        /// Új játék betöltésének eseménykiváltása.
        /// </summary>
        private void OnNewGame()
        {
            Score = 0;
            NewGame?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// Játék elindításának eseménykiváltása.
        /// </summary>
        private void OnStartGame()
        {
            Score = 0;
            StartGame?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// ViewModell gameover esemény kiváltása
        /// </summary>
        private void OnViewModelGameOver()
        {
            ViewModelGameOver?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// Quit esemény kiváltása
        /// </summary>
        private void OnQuit()
        {
            Quit?.Invoke(this, EventArgs.Empty);
        }

        #endregion

    }
}
