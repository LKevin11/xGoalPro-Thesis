using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using MineSweeper.Model;
using MineSweeper.Persistence;

namespace MineSweeper.Model
{
    public class MineSweeperModel
    {

        #region Private Fields

        private Int32 _rows;
        private Int32 _columns;
        private Int32 _mineCount;
        private Cell[,]? _grid;
        private IFileManager? _fileManager;

        #endregion


        #region Public Properties

        /// <summary>
        /// Property for row count
        /// </summary>
        public Int32 Rows { get { return _rows; } private set { _rows = value; } }

        /// <summary>
        /// Property for column count
        /// </summary>
        public Int32 Columns { get { return _columns; } private set { _columns = value; } }

        /// <summary>
        /// Property for minecount
        /// </summary>
        public Int32 MineCount { get { return _mineCount; } private set { _mineCount = value; } }

        /// <summary>
        /// MineSweeper map
        /// </summary>
        public Cell[,] Grid { get { return _grid!; } }

        /// <summary>
        /// Persistence
        /// </summary>
        public IFileManager? FileManager { get { return _fileManager; } }

        #endregion


        #region Constructor

        /// <summary>
        /// Constructor for model
        /// </summary>
        /// <param name="row">number of rows</param>
        /// <param name="col">number of columns</param>
        /// <param name="count">number of mines</param>
        /// <param name="fileManager">persistence</param>
        public MineSweeperModel(Int32 row, Int32 col, Int32 count, IFileManager fileManager)
        {

            this._fileManager = fileManager;

            this._rows = row;
            this._columns = col;
            this._mineCount = count;

            this._grid = new Cell[row, col];

            InitializeCells();
            PlaceMines();
            CalculateAdjacentMines();
        }

        #endregion


        #region Private Methods

        /// <summary>
        /// Initialize cells with Cell class
        /// </summary>
        private void InitializeCells()
        {

            for (int i = 0; i < _rows; ++i)
            {
                for (int j = 0; j < _columns; ++j)
                {
                    _grid![i, j] = new Cell();
                }
            }

        }

        /// <summary>
        /// Places mines at random positions
        /// </summary>
        private void PlaceMines()
        {

            Random random = new Random();
            int placedMines = 0;

            while (placedMines < _mineCount)
            {

                int row = random.Next(_rows);
                int col = random.Next(_columns);

                if (!_grid![row, col].HasMine)
                {
                    _grid[row, col].HasMine = true;
                    ++placedMines;
                }

            }

        }

        /// <summary>
        /// Calculates adjacent mines for each cell
        /// </summary>
        private void CalculateAdjacentMines()
        {

            for (int row = 0; row < _rows; row++)
            {
                for (int col = 0; col < _columns; ++col)
                {

                    if (_grid![row, col].HasMine) continue;

                    int adjacentMines = 0;

                    for (int dr = -1; dr <= 1; ++dr)
                    {
                        for (int dc = -1; dc <= 1; dc++)
                        {

                            int r = row + dr;
                            int c = col + dc;

                            if (r >= 0 && r < _rows && c >= 0 && c < _columns && _grid![r, c].HasMine)
                            {
                                adjacentMines++;
                            }

                        }
                    }

                    _grid![row, col].AdjacentMines = adjacentMines;
                }
            }

        }

        /// <summary>
        /// Makes field visible (recursive function)
        /// </summary>
        /// <param name="row">row coordinate</param>
        /// <param name="col">column coordinate</param>
        private void RevealCell(int row, int col)
        {

            var cell = _grid![row, col];

            if (cell.IsRevealed) return;

            cell.IsRevealed = true;

            if (cell.HasMine)
            {
                return;
            }

            if (cell.AdjacentMines == 0)
            {
                for (int dr = -1; dr <= 1; dr++)
                {
                    for (int dc = -1; dc <= 1; dc++)
                    {
                        int newRow = row + dr;
                        int newCol = col + dc;
                        if (newRow >= 0 && newRow < _rows && newCol >= 0 && newCol < _columns)
                        {
                            RevealCell(newRow, newCol);
                        }
                    }
                }
                return;
            }

            return;

        }

        /// <summary>
        /// Checks winning state
        /// </summary>
        /// <returns>true if player won else false</returns>
        private bool CheckWin()
        {

            int count = 0;
            for (int i = 0; i < _rows; i++)
            {
                for (int j = 0; j < _columns; j++)
                {

                    if (!(_grid![i, j].IsRevealed)) count++;

                }
            }

            return count == _mineCount;
        }

        #endregion


        #region Public Methods

        /// <summary>
        /// Makes field visible (entry point for recursive function)
        /// </summary>
        /// <param name="row">row coordinate</param>
        /// <param name="col">column coordinate</param>
        public void Reveal(int row, int col)
        {

            if (_grid![row, col].IsMarked) return;

            if (_grid![row, col].HasMine)
            {
                OnGameOver();
                return;
            }

            RevealCell(row, col);

            if (CheckWin())
            {
                OnWin();
            }

            OnRefresh();
        }

        /// <summary>
        /// Returns all bomb coordinates
        /// </summary>
        /// <returns>All bomb coordinates</returns>
        public IEnumerable<(int row, int col)> GetAllBombs()
        {

            for (int row = 0; row < _rows; row++)
            {
                for (int col = 0; col < _columns; col++)
                {
                    if (_grid![row, col].HasMine)
                    {
                        yield return (row, col);
                    }
                }
            }

        }

        /// <summary>
        /// Mark field
        /// </summary>
        /// <param name="row">row coordinate</param>
        /// <param name="col">column coordinate</param>
        public void Mark(int row, int col)
        {

            if (_grid![row, col].IsMarked)
            {
                _grid![row, col].IsMarked = false;
                OnMarkCell(row, col, false);
            }
            else
            {
                _grid![row, col].IsMarked = true;
                OnMarkCell(row, col, true);
            }

        }

        /// <summary>
        /// Saves data
        /// </summary>
        /// <param name="data">Data for persistence</param>
        public void SaveData(OutputData data)
        {

            if (_fileManager!.SaveFile(data))
            {
                //Success
                return;
            }
            else
            {
                OnFileManagerError();
            }

        }

        #endregion


        #region Events

        public event EventHandler? GameOver;
        public event EventHandler? Refresh;
        public event EventHandler<MarkCellEventArgs>? MarkCell;
        public event EventHandler? Win;
        public event EventHandler? FileManagerError;

        #endregion


        #region Event Triggers

        public void OnGameOver()
        {
            GameOver?.Invoke(this, EventArgs.Empty);
        }

        public void OnRefresh()
        {
            Refresh?.Invoke(this, EventArgs.Empty);
        }

        public void OnMarkCell(int row, int col, bool b)
        {
            MarkCell?.Invoke(this, new MarkCellEventArgs(row,col,b));
        }

        public void OnWin()
        {
            Win?.Invoke(this, EventArgs.Empty);
        }

        public void OnFileManagerError()
        {
            FileManagerError?.Invoke(this, EventArgs.Empty);
        }

        #endregion


    }
}
