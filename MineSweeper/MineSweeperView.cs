using MineSweeper.Model;
using MineSweeper.Persistence;
using System.Reflection;

namespace MineSweeper
{
    public partial class MineSweeperView : Form
    {
        #region Private Fields

        private MineSweeperModel? _model;
        private Button[,]? _buttons;

        private RadioButton? _rbEasy;
        private RadioButton? _rbMedium;
        private RadioButton? _rbHard;
        private Button? _quitBtn;
        private Button? _btnStart;

        private TableLayoutPanel? _radioPanel;
        private TableLayoutPanel? _gameBoardPanel;
        private Panel? _mainPanel;

        private System.Windows.Forms.Timer? _timer;
        private Int32 _elapsedTime = 0;
        private Label? _timerLabel;

        private Font _cellFont;
        private Color[] _numberColors = {
            Color.Blue,          // 1
            Color.Green,         // 2
            Color.Red,           // 3
            Color.DarkBlue,      // 4
            Color.DarkRed,       // 5
            Color.Teal,          // 6
            Color.Black,         // 7
            Color.Gray           // 8
        };

        #endregion

        #region Constructor

        /// <summary>
        /// View constructor
        /// </summary>
        public MineSweeperView()
        {
            InitializeComponent();

            string? exeDir = Path.GetDirectoryName(Application.ExecutablePath);
            this.Icon = new Icon(Path.Combine(exeDir!, "icon.ico"));

            this.WindowState = FormWindowState.Maximized;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.BackColor = ColorTranslator.FromHtml("#0d1b2a");

            // Create a font that will scale well with different cell sizes
            _cellFont = new Font("Arial", 12, FontStyle.Bold);
        }

        #endregion

        #region Private Methods

        /// <summary>
        /// Initialize static UI elements
        /// </summary>
        private void InitializeGameSetupUI()
        {
            // Create main panel for better organization
            _mainPanel = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = ColorTranslator.FromHtml("#1b263b"),
                Padding = new Padding(10)
            };
            this.Controls.Add(_mainPanel);

            // Title label
            Label titleLabel = new Label
            {
                Text = "MINESWEEPER",
                Dock = DockStyle.Top,
                Height = 60,
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Arial", 24, FontStyle.Bold),
                ForeColor = ColorTranslator.FromHtml("#00b87b") // neon green title
            };
            _mainPanel.Controls.Add(titleLabel);

            // Radio button panel
            _radioPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Top,
                Height = 50,
                BackColor = ColorTranslator.FromHtml("#0d1b2a"),
                CellBorderStyle = TableLayoutPanelCellBorderStyle.Single,
                Padding = new Padding(5)
            };

            _radioPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 33.33f));
            _radioPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 33.33f));
            _radioPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 33.33f));

            _rbEasy = new RadioButton
            {
                Text = "Easy (8x8, 10 mines)",
                Dock = DockStyle.Fill,
                Checked = true,
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Arial", 10, FontStyle.Regular),
                ForeColor = ColorTranslator.FromHtml("#e0e1dd"),
                BackColor = ColorTranslator.FromHtml("#0d1b2a")
            };

            _rbMedium = new RadioButton
            {
                Text = "Medium (14x14, 30 mines)",
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Arial", 10, FontStyle.Regular),
                ForeColor = ColorTranslator.FromHtml("#e0e1dd"),
                BackColor = ColorTranslator.FromHtml("#0d1b2a")
            };

            _rbHard = new RadioButton
            {
                Text = "Hard (18x18, 40 mines)",
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Arial", 10, FontStyle.Regular),
                ForeColor = ColorTranslator.FromHtml("#e0e1dd"),
                BackColor = ColorTranslator.FromHtml("#0d1b2a")
            };

            _radioPanel.Controls.Add(_rbEasy, 0, 0);
            _radioPanel.Controls.Add(_rbMedium, 1, 0);
            _radioPanel.Controls.Add(_rbHard, 2, 0);
            _mainPanel.Controls.Add(_radioPanel);

            // Button panel
            TableLayoutPanel buttonPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Top,
                Height = 50,
                BackColor = Color.Transparent
            };

            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));

            _btnStart = new Button
            {
                Text = "Start Game",
                Dock = DockStyle.Fill,
                Height = 40,
                BackColor = ColorTranslator.FromHtml("#00b87b"),
                ForeColor = ColorTranslator.FromHtml("#0d1b2a"),
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Arial", 10, FontStyle.Bold)
            };
            _btnStart.FlatAppearance.BorderSize = 0;
            _btnStart.Click += BtnStart_Click;
            buttonPanel.Controls.Add(_btnStart, 0, 0);

            _quitBtn = new Button
            {
                Text = "Quit",
                Dock = DockStyle.Fill,
                Height = 40,
                BackColor = ColorTranslator.FromHtml("#415a77"),
                ForeColor = ColorTranslator.FromHtml("#e0e1dd"),
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Arial", 10, FontStyle.Bold)
            };
            _quitBtn.FlatAppearance.BorderSize = 0;
            _quitBtn.Click += QuitBtn_Click;
            buttonPanel.Controls.Add(_quitBtn, 1, 0);

            _mainPanel.Controls.Add(buttonPanel);

            // Timer label
            _timerLabel = new Label
            {
                Text = "Time: 00:00",
                Dock = DockStyle.Top,
                Height = 30,
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Arial", 12, FontStyle.Bold),
                ForeColor = ColorTranslator.FromHtml("#a9bcd0")
            };
            _mainPanel.Controls.Add(_timerLabel);
        }


        private void InitializeWelcomeBoard()
        {
            // Remove old game board if exists
            if (_gameBoardPanel != null)
            {
                _mainPanel!.Controls.Remove(_gameBoardPanel);
                _gameBoardPanel.Dispose();
            }

            // Create a panel to hold the welcome message
            _gameBoardPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                BackColor = Color.LightBlue,
                RowCount = 1,
                ColumnCount = 1,
                Margin = new Padding(10)
            };

            _gameBoardPanel.SuspendLayout();

            // Welcome label
            Label welcomeLabel = new Label
            {
                Text = "Welcome to Minesweeper!\nClick 'Start Game' to begin.\nLeft-click to reveal, Right-click to flag mines.",
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleCenter,
                Font = new Font("Arial", 16, FontStyle.Bold),
                ForeColor = Color.DarkBlue
            };

            _gameBoardPanel.Controls.Add(welcomeLabel, 0, 0);

            _gameBoardPanel.ResumeLayout(false);

            _mainPanel!.Controls.Add(_gameBoardPanel);
            _gameBoardPanel.BringToFront();
        }

        /// <summary>
        /// Create model and start game
        /// </summary>
        /// <param name="rows">number of rows</param>
        /// <param name="columns">number of columns</param>
        /// <param name="mines">number of mines</param>
        private void StartGame(int rows, int columns, int mines)
        {
            // Initialize timer
            if (_timer != null)
            {
                _timer.Stop();
                _elapsedTime = 0;
            }

            _timer = new System.Windows.Forms.Timer
            {
                Interval = 1000
            };
            _timer.Tick += TimerTick;

            // --- Create the model first ---
            IFileManager fileManager = new TextFileManager();
            _model = new MineSweeperModel(rows, columns, mines, fileManager);

            // Connect event handlers
            _model.Refresh += new EventHandler(UpdateView);
            _model.GameOver += new EventHandler(ShowGameOver);
            _model.MarkCell += new EventHandler<MarkCellEventArgs>(MarkCellEventHandler);
            _model.Win += new EventHandler(Win);
            _model.FileManagerError += new EventHandler(FileManagerErrorEventHandler);

            // --- Now create the game board UI ---
            InitializeGameBoard(rows, columns);

            // Force initial sync so grid is consistent with model immediately
            UpdateView(this, EventArgs.Empty);

            // Start the timer
            _timer.Start();
        }

        /// <summary>
        /// Initialize game board UI elements (hidden initially)
        /// </summary>
        /// <param name="rows">number of rows</param>
        /// <param name="columns">number of columns</param>
        private void InitializeGameBoard(int rows, int columns)
        {
            if (_gameBoardPanel != null)
            {
                _mainPanel!.Controls.Remove(_gameBoardPanel);
                _gameBoardPanel.Dispose();
            }

            _buttons = new Button[rows, columns];

            _gameBoardPanel = new TableLayoutPanel
            {
                RowCount = rows,
                ColumnCount = columns,
                Dock = DockStyle.Fill,
                BackColor = ColorTranslator.FromHtml("#1b263b"),
                Margin = new Padding(10),
                Visible = false
            };

            // 🚀 Enable double buffering to prevent flicker
            _gameBoardPanel.GetType().GetProperty("DoubleBuffered",
                System.Reflection.BindingFlags.NonPublic |
                System.Reflection.BindingFlags.Instance)!
                .SetValue(_gameBoardPanel, true, null);

            _gameBoardPanel.SuspendLayout();

            int minDimension = Math.Min(rows, columns);
            int fontSize = Math.Max(8, Math.Min(16, 200 / minDimension));
            _cellFont = new Font("Arial", fontSize, FontStyle.Bold);

            for (int i = 0; i < rows; i++)
                _gameBoardPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100f / rows));

            for (int j = 0; j < columns; j++)
                _gameBoardPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f / columns));

            for (int row = 0; row < rows; row++)
            {
                for (int col = 0; col < columns; col++)
                {
                    var button = new Button
                    {
                        Dock = DockStyle.Fill,
                        Margin = new Padding(2),
                        Tag = new Tuple<int, int>(row, col),
                        BackColor = ColorTranslator.FromHtml("#415a77"),
                        FlatStyle = FlatStyle.Flat,
                        Font = _cellFont,
                        ForeColor = ColorTranslator.FromHtml("#e0e1dd"),
                        Text = ""
                    };
                    button.FlatAppearance.BorderColor = ColorTranslator.FromHtml("#0d1b2a");
                    button.FlatAppearance.BorderSize = 1;
                    button.MouseDown += Button_Click;
                    _buttons[row, col] = button;
                    _gameBoardPanel.Controls.Add(button, col, row);
                }
            }

            _gameBoardPanel.ResumeLayout(false);

            _mainPanel!.Controls.Add(_gameBoardPanel);
            _gameBoardPanel.BringToFront();

            _gameBoardPanel.Visible = true; // show only when ready

            _gameBoardPanel.Resize += GameBoardPanel_Resize;
            AdjustButtonSizes();
        }


        private void GameBoardPanel_Resize(object? sender, EventArgs e)
        {
            AdjustButtonSizes();
        }

        private void AdjustButtonSizes()
        {
            if (_buttons == null || _gameBoardPanel == null) return;

            int rows = _buttons.GetLength(0);
            int cols = _buttons.GetLength(1);

            // Calculate square size that fits in panel
            int cellWidth = _gameBoardPanel.Width / cols;
            int cellHeight = _gameBoardPanel.Height / rows;
            int size = Math.Min(cellWidth, cellHeight) - 4; // Account for margin

            // Update font size based on cell size
            int fontSize = Math.Max(8, Math.Min(16, size / 2));
            _cellFont = new Font("Arial", fontSize, FontStyle.Bold);

            for (int r = 0; r < rows; r++)
            {
                for (int c = 0; c < cols; c++)
                {
                    _buttons[r, c].Width = size;
                    _buttons[r, c].Height = size;
                    _buttons[r, c].Font = _cellFont;
                }
            }
        }

        /// <summary>
        /// Disable all gamefield buttons
        /// </summary>
        private void DisableAllButtons()
        {
            for (int row = 0; row < _model!.Rows; row++)
            {
                for (int col = 0; col < _model!.Columns; col++)
                {
                    if (_buttons![row, col].Enabled)
                    {
                        _buttons[row, col].BackColor = Color.Gray;
                    }
                    _buttons![row, col].Enabled = false;
                }
            }
        }

        #endregion

        #region View EventHandlers

        private void QuitBtn_Click(object? sender, EventArgs e)
        {
            Application.Exit();
        }

        /// <summary>
        /// Event handler for form's load event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void MineSweeperView_Load(object sender, EventArgs e)
        {
            InitializeGameSetupUI();
            InitializeWelcomeBoard();
        }

        /// <summary>
        /// Event handler for start button's click event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void BtnStart_Click(object? sender, EventArgs e)
        {
            int rows = 0, columns = 0, mines = 0;

            if (_rbEasy!.Checked)
            {
                rows = 8;
                columns = 8;
                mines = 10;
            }
            else if (_rbMedium!.Checked)
            {
                rows = 14;
                columns = 14;
                mines = 30;
            }
            else if (_rbHard!.Checked)
            {
                rows = 18;
                columns = 18;
                mines = 40;
            }

            StartGame(rows, columns, mines);
        }

        /// <summary>
        /// Event handler for gamefield button's click event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void Button_Click(object? sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
            {
                Button? button = sender as Button;
                if (button == null) return;

                var (row, col) = (Tuple<int, int>)button.Tag;
                _model!.Reveal(row, col);
            }
            else if (e.Button == MouseButtons.Right)
            {
                Button? button = sender as Button;
                if (button == null) return;

                var (row, col) = (Tuple<int, int>)button.Tag;
                _model!.Mark(row, col);
            }
        }

        /// <summary>
        /// Event handler for timer's tick event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void TimerTick(object? sender, EventArgs e)
        {
            _elapsedTime++;
            int minutes = _elapsedTime / 60;
            int seconds = _elapsedTime % 60;
            _timerLabel!.Text = $"Time: {minutes:D2}:{seconds:D2}";
        }

        #endregion

        #region Model EventHandlers

        /// <summary>
        /// Event handler for model's refresh event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void UpdateView(object? sender, EventArgs e)
        {
            // Suspend layout to prevent flickering
            _gameBoardPanel!.SuspendLayout();

            for (int row = 0; row < _model!.Rows; row++)
            {
                for (int col = 0; col < _model!.Columns; col++)
                {
                    var cell = _model!.Grid[row, col];
                    if (cell.IsRevealed)
                    {
                        _buttons![row, col].Enabled = false;
                        _buttons![row, col].FlatAppearance.BorderSize = 0;
                        _buttons![row, col].BackColor = ColorTranslator.FromHtml("#1e324e");
                        _buttons![row, col].ForeColor = ColorTranslator.FromHtml("#e0e1dd");

                        if (cell.HasMine)
                        {
                            _buttons![row, col].Text = "X";
                            _buttons![row, col].ForeColor = ColorTranslator.FromHtml("#ff4d4d");
                        }
                        else if (cell.AdjacentMines > 0)
                        {
                            _buttons![row, col].Text = cell.AdjacentMines.ToString();
                            // Set color based on the number
                            if (cell.AdjacentMines <= _numberColors.Length)
                            {
                                _buttons![row, col].ForeColor = ColorTranslator.FromHtml("#00b87b");
                            }
                        }
                        else
                        {
                            _buttons![row, col].Text = "";
                        }
                    }
                }
            }

            // Resume layout after all updates are done
            _gameBoardPanel.ResumeLayout();
        }

        /// <summary>
        /// Event handler for model's markcell event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void MarkCellEventHandler(object? sender, MarkCellEventArgs e)
        {
            if (!e.Flag)
            {
                // Unflagged cell
                _buttons![e.Row, e.Column].BackColor = ColorTranslator.FromHtml("#415a77"); // normal button background
                _buttons![e.Row, e.Column].ForeColor = ColorTranslator.FromHtml("#e0e1dd");
                _buttons![e.Row, e.Column].Text = "";
            }
            else
            {
                // Flagged cell
                _buttons![e.Row, e.Column].BackColor = ColorTranslator.FromHtml("#00b87b"); // neon green accent
                _buttons![e.Row, e.Column].ForeColor = ColorTranslator.FromHtml("#0d1b2a"); // dark navy text
                _buttons![e.Row, e.Column].Font = new Font("Arial", _buttons[e.Row, e.Column].Font.Size, FontStyle.Bold);
                _buttons![e.Row, e.Column].Text = "F";
            }
        }

        /// <summary>
        /// Event handler for model's win event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void Win(object? sender, EventArgs e)
        {
            _timer!.Stop();
            MessageBox.Show($"All mines found! You won in {_elapsedTime} seconds!", "Win",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
            DisableAllButtons();

            SaveFileDialog saveFileDialog = new SaveFileDialog();
            saveFileDialog.Filter = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*";
            saveFileDialog.Title = "Save Game Results";

            if (saveFileDialog.ShowDialog() == DialogResult.OK)
            {
                string filename = saveFileDialog.FileName;
                string date = DateTime.Now.ToString();
                string score = _elapsedTime.ToString();

                OutputData data = new OutputData(filename, date, score);
                _model!.SaveData(data);
            }
        }

        /// <summary>
        /// Event handler for model's gameover event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void ShowGameOver(object? sender, EventArgs e)
        {
            _timer!.Stop();

            // Suspend layout to prevent flickering
            _gameBoardPanel!.SuspendLayout();

            foreach (var (row, col) in _model!.GetAllBombs())
            {
                _buttons![row, col].Text = "X";
                _buttons![row, col].ForeColor = Color.Red;
                _buttons![row, col].BackColor = Color.White;
            }

            // Resume layout after all updates are done
            _gameBoardPanel.ResumeLayout();

            MessageBox.Show("Game Over! You hit a mine.", "Game Over",
                MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
            DisableAllButtons();
        }

        /// <summary>
        /// Event handler for model's FileManagerError event
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void FileManagerErrorEventHandler(object? sender, EventArgs e)
        {
            MessageBox.Show("Saving error!", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }

        #endregion
    }
}