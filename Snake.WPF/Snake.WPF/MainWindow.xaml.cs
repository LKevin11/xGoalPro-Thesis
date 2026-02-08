using Snake.Model.Model;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace Snake.WPF
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {

        /*private readonly int Rows =  15, Cols = 15;
        private readonly Rectangle[,] gridContent;
        private GameModel gameModel;*/
        
        public MainWindow()
        {
            InitializeComponent();

            //gridContent = SetupGrid();
            //gameModel = new GameModel(Rows,Cols);
        }

        /*private async void Window_Loaded(object sender, RoutedEventArgs e)
        {

            Draw();
            await GameLoop();

        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if (gameModel.GameOver)
            {
                return;
            }

            switch (e.Key)
            {

                case Key.Left:
                    gameModel.ChangeDirection(Direction.Left); break;
                case Key.Right:
                    gameModel.ChangeDirection(Direction.Right); break;
                case Key.Up:
                    gameModel.ChangeDirection(Direction.Up); break;
                case Key.Down:
                    gameModel.ChangeDirection(Direction.Down); break;

            }

        }

        private async Task GameLoop()
        {
            while(!gameModel.GameOver)
            {
                await Task.Delay(100);
                gameModel.Move();
                Draw();
            }
        }

        private Rectangle[,] SetupGrid()
        {

            Rectangle[,] content = new Rectangle[Rows, Cols];
            GameGrid.Rows = Rows;
            GameGrid.Columns = Cols;

            for(int r = 0; r < Rows; r++)
            {
                for(int c = 0; c < Cols; c++)
                {
                    Rectangle empty = new Rectangle();
                    empty.Fill = Brushes.Gray;
                    empty.Margin = new Thickness(1);

                    content[r,c] = empty;
                    GameGrid.Children.Add(empty);
                }
            }

            return content;
        }

        private void Draw()
        {
            DrawGrid();
            ScoreText.Text = $"Score {gameModel.Score}";
        }

        private void DrawGrid()
        {

            for(int r = 0;r < Rows; r++)
            {
                for(int c = 0; c < Cols; c++)
                {
                    GridValue gridVal = gameModel!.Grid![r,c];

                    if (gameModel.Grid[r,c] == GridValue.Empty)
                    {
                        gridContent[r,c].Fill = Brushes.Gray;
                    }
                    else if (gameModel.Grid[r,c] == GridValue.Snake)
                    {
                        gridContent[r, c].Fill = Brushes.Green;
                    }
                    else if (gameModel.Grid[r,c] == GridValue.Food)
                    {
                        gridContent[r, c].Fill = Brushes.Red;
                    }

                }
            }

        }

        */
    }
}