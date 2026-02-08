using Snake.Model.Persistence;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace Snake.Model.Model
{
    /// <summary>
    /// Játékmodell osztálya
    /// </summary>
    public class GameModel
    {

        #region Private Fields

        private readonly LinkedList<Direction> _dirChanges; //irányváltások
        private readonly LinkedList<Position> _snakepositions; //kígyó pozíciók
        private readonly List<Position> _barrierpositions; //akadály pozíciók
        private readonly Random _random;
        private readonly IFileManager? _fileManager; //perzisztencia

        #endregion


        #region Public Properties

        /// <summary>
        /// Sorok
        /// </summary>
        public int Rows { get; set; }
        /// <summary>
        /// Oszlopok
        /// </summary>
        public int Cols { get; set; }
        /// <summary>
        /// Játékmező
        /// </summary>
        public GridValue[,]? Grid { get; set; }
        /// <summary>
        /// Irány
        /// </summary>
        public Direction? Direction { get; set; }
        /// <summary>
        /// Elfogyasztott tojások száma
        /// </summary>
        public int Score { get; set; }
        /// <summary>
        /// Vége van-e a játéknak
        /// </summary>
        public bool IsGameOver {  get; set; }
        /// <summary>
        /// Játékmező nagysága
        /// </summary>
        public GameFieldSize Size { get; set; }
        /// <summary>
        /// Fut-e a játék
        /// </summary>
        public bool IsRunning { get; set; }

        /// <summary>
        /// Akadály pozíciók
        /// </summary>
        public List<Position> BarrierPositions
        {
            get { return _barrierpositions; }
        }

        /// <summary>
        /// Irányváltások listája
        /// </summary>
        public LinkedList<Direction> DirChanges
        {
            get { return _dirChanges; }
        }

        /// <summary>
        /// Kígyó pozíciójának listája
        /// </summary>
        public LinkedList<Position> SnakePositions
        {
            get { return _snakepositions; }
        }

        #endregion


        #region Events

        /// <summary>
        /// Játék vége esemény.
        /// </summary>
        public event EventHandler? GameOver;

        /// <summary>
        /// Tojás fogyasztása esemény.
        /// </summary>
        public event EventHandler? Eating;

        /// <summary>
        /// Fut-e az időzítő esemény.
        /// </summary>
        public event EventHandler<GameLoopEventArgs>? GameLoopChanged;

        /// <summary>
        /// Kígyó elmozgott esemény.
        /// </summary>
        public event EventHandler? RefreshEvent;

        /// <summary>
        /// Modell betöltött esemény
        /// </summary>
        public event EventHandler? GameLoaded;

        #endregion


        #region Constructors

        /// <summary>
        /// Játékmodell konstruktor
        /// </summary>
        /// <param name="fileManager">Perzisztencia</param>
        public GameModel(IFileManager? fileManager)
        {
            _random = new Random();
            _dirChanges = new LinkedList<Direction>();
            _snakepositions = new LinkedList<Position>();
            _barrierpositions = new List<Position>();
            _fileManager = fileManager;

            Grid = new GridValue[Rows, Cols];
            Size = GameFieldSize.SMALL;
            Direction = Direction.Right;
            Score = 0;
            IsGameOver = true;
            IsRunning = false;
        }

        #endregion


        #region Public Methods

        /// <summary>
        /// Fejpozíció
        /// </summary>
        /// <returns>Fejpozíció</returns>
        public Position HeadPosition()
        {
            return _snakepositions!.First!.Value;
        }

        /// <summary>
        /// Farokpozíció
        /// </summary>
        /// <returns>Farokpozíció</returns>
        public Position TailPosition()
        {
            return _snakepositions!.Last!.Value;
        }

        /// <summary>
        /// Kígyó pozíciói
        /// </summary>
        /// <returns>Pozíció halmaz</returns>
        public IEnumerable<Position> SnakePosition()
        {
            return _snakepositions;
        }

        /// <summary>
        /// Irányváltás
        /// </summary>
        /// <param name="direction">Irány</param>
        public void ChangeDirection(Direction direction)
        {
            if(CanChangeDirection(direction))
            {
                _dirChanges.AddLast(direction);
            }
        }  

        /// <summary>
        /// Elmozdulás, step
        /// </summary>
        public void Move()
        {

            if(_dirChanges.Count > 0)
            {
                Direction = _dirChanges!.First!.Value;
                _dirChanges.RemoveFirst();
            }

            Position newHeadPos = HeadPosition().Translate(Direction!);
            GridValue hit = WillHit(newHeadPos);

            if(hit == GridValue.Outside || hit == GridValue.Snake)
            {
                IsGameOver = true;
                OnGameOver();
            }
            else if (hit == GridValue.Empty)
            {
                RemoveTail();
                AddHead(newHeadPos);
            }
            else if(hit == GridValue.Food)
            {
                AddHead(newHeadPos);
                Score++;
                AddFood();
                FoundFood();
            }
        }

        /// <summary>
        /// Játék betöltése.
        /// </summary>
        /// <param name="size">Pálya mérete</param>
        public void Load(GameFieldSize size)
        {

            _snakepositions.Clear();
            _dirChanges.Clear();
            _barrierpositions.Clear();

            Score = 0;

            string[] data = _fileManager!.Load(size)!.Split(' ');

            Rows = int.Parse(data[0]);
            Cols = int.Parse(data[1]);

            Grid = new GridValue[Rows, Cols];

            for(int i = 2; i < data.Length; i+= 2)
            {

                int r = int.Parse(data[i]);
                int c = int.Parse(data[i+1]);

                _barrierpositions.Add( new Position(r,c));
                Grid[r, c] = GridValue.Outside;

            }

            Direction = Direction.Right;

            AddSnake();
            AddFood();

            OnGameLoaded();
        }

        /// <summary>
        /// Új játék kezdése.
        /// </summary>
        public async void RestartGame()
        {

            _snakepositions.Clear();
            _dirChanges.Clear();
            Grid = new GridValue[Rows, Cols];

            for(int i = 0; i < _barrierpositions.Count; i++)
            {

                Grid[_barrierpositions[i].Row, _barrierpositions[i].Column] = GridValue.Outside;

            }

            Direction = Direction.Right;

            Score = 0;

            AddSnake();
            AddFood();
            
            IsGameOver = false;
            IsRunning = true;

            await GameLoop();

        }

        /// <summary>
        /// Szünet kezelése
        /// </summary>
        public void ManagePause()
        {

            if(IsRunning)
            {
                IsRunning = false;
                OnGameTimerChangedEvent(false);
            }
            else
            {
                IsRunning = true;
                OnGameTimerChangedEvent(true);
            }

        }

        #endregion


        #region Private Methods
        
        /// <summary>
        /// Játék időzítője
        /// </summary>
        private async Task GameLoop()
        {
            while (!IsGameOver)
            {
                             

                await Task.Delay(100);

                if(!IsRunning) { continue; }

                Move();
                Refresh();
            }
        }

        /// <summary>
        /// Kígyó hozzáadása
        /// </summary>
        private void AddSnake()
        {
            int r = Rows / 2;

            for(int c = 1; c < 6; c++)
            {
                Grid![r, c] = GridValue.Snake;
                _snakepositions.AddFirst(new Position(r, c));
            }
        }

        /// <summary>
        /// Üres pozíció keresése
        /// </summary>
        /// <returns>Üres pozíció</returns>
        private IEnumerable<Position> EmptyPosition()
        {
            for(int r = 0; r < Rows; r++)
            {
                for(int c = 0; c< Cols; c++)
                {
                    if (Grid![r,c] == GridValue.Empty)
                    {
                        yield return new Position(r, c);
                    }
                }
            }
        }

        /// <summary>
        /// Tojás hozzáadása
        /// </summary>
        private void AddFood()
        {
            List<Position> empty = new List<Position>(EmptyPosition());

            if(empty.Count == 0)
            {
                return;
            }

            Position pos = empty[_random.Next(empty.Count)];
            Grid![pos.Row,pos.Column] = GridValue.Food;


        }

        /// <summary>
        /// Fejhozzáadása
        /// </summary>
        /// <param name="pos">Pozíció</param>
        private void AddHead(Position pos)
        {
            _snakepositions.AddFirst(pos);
            Grid![pos.Row, pos.Column] = GridValue.Snake;
        }

        /// <summary>
        /// Farok törlése
        /// </summary>
        private void RemoveTail()
        {
            Position tail = _snakepositions.Last!.Value;
            Grid![tail.Row, tail.Column] = GridValue.Empty;
            _snakepositions.RemoveLast();
        }

        /// <summary>
        /// Utolsó irányváltás
        /// </summary>
        private Direction GetLastDirection()
        {
            if(_dirChanges.Count == 0)
            {
                return Direction!;
            }

            return _dirChanges!.Last!.Value;
        }

        /// <summary>
        /// Irányváltás ellenőrzése
        /// </summary>
        /// <param name="newdir">Irány</param>
        /// <returns>Valid-e az irányváltás</returns>
        private bool CanChangeDirection(Direction newdir)
        {
            if(_dirChanges.Count == 2)
            {
                return false;
            }

            Direction lastdir = GetLastDirection();

            return newdir != lastdir && newdir != lastdir.Opposite();
        }

        /// <summary>
        /// Akadályba ütközés ellenőrzés
        /// </summary>
        /// <param name="position">Pozíció</param>
        /// <returns></returns>
        private bool OutsideGrid(Position position)
        {
            bool b = false;

            foreach(var barrier in _barrierpositions)
            {
                if(barrier.Row == position.Row && barrier.Column == position.Column) b = true;
            }


            return position.Row < 0 || position.Row >= Rows || position.Column < 0 || position.Column >= Cols || b;
        }

        /// <summary>
        /// Adott pozícióban a játékmező értékének lekérdezése
        /// </summary>
        /// <param name="newHeadPos">Új fejpozíció</param>
        /// <returns>Játékmező érték</returns>
        private GridValue WillHit(Position newHeadPos)
        {

            if (OutsideGrid(newHeadPos))
            {
                return GridValue.Outside;
            }

            if(newHeadPos == TailPosition())
            {
                return GridValue.Empty;
            }
            
            return Grid![newHeadPos.Row, newHeadPos.Column];
        }

        #endregion


        #region Event Triggers

        /// <summary>
        /// Játék vége esemény kiváltása.
        /// </summary>
        private void OnGameOver()
        {
            GameOver?.Invoke(this, EventArgs.Empty);

        }

        /// <summary>
        /// Tojás találása esemény kiváltása.
        /// </summary>
        private void FoundFood()
        {
            Eating?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// Szünet kezelésének eseménykiváltása.
        /// </summary>
        /// <param name="b">Fut-e az időzítő igaz/hamis érték</param>
        private void OnGameTimerChangedEvent(bool b)
        {
            GameLoopChanged?.Invoke(this, new GameLoopEventArgs(b));
        }

        /// <summary>
        /// Kígyó elmozdult esemény kiváltása.
        /// </summary>
        private void Refresh()
        {
            RefreshEvent?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// Játék betölött esemény kiváltása
        /// </summary>
        private void OnGameLoaded()
        {
            GameLoaded?.Invoke(this, EventArgs.Empty);
        }

        #endregion

    }
}
