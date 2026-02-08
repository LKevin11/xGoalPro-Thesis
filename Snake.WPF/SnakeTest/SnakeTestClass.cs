using System;
using Snake.Model.Persistence;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Moq;
using Snake.Model.Model;

namespace SnakeTest
{
    [TestClass]
    public class SnakeModelTest
    {

        private GameModel? _model = null;
        private Mock<IFileManager>? _mock = null;

        [TestInitialize]
        public void InitSnakeModelTest()
        {
            _mock = new Mock<IFileManager>();
            _model = new GameModel(_mock.Object);
        }

        public void MockandLoadText(string text)
        {
            _mock!.Setup(fileManager => fileManager.Load(GameFieldSize.MEDIUM)).Returns(text);
            _model!.Load(GameFieldSize.MEDIUM);
        }



        [TestMethod]
        public void TestFileLoading()
        {

            MockandLoadText("20 20 5 10 6 10");

            Assert.AreEqual(20, _model!.Rows);
            Assert.AreEqual(2, _model?.BarrierPositions?.Count);

        }

        [TestMethod]
        [ExpectedException(typeof(Exception))]
        public void TestFileLoadingWithException()
        {
            _mock!.Setup(fileManager => fileManager.Load(GameFieldSize.MEDIUM)).Returns(() => throw new Exception());
            _model!.Load(GameFieldSize.MEDIUM);
        }

        [TestMethod]
        public void MoveDownTest()
        {
            MockandLoadText("20 20 5 10 6 10");

            _model!.ChangeDirection(Direction.Down);
            _model!.Move();

            Assert.AreEqual(Direction.Down.RowOffset, _model!.Direction!.RowOffset);
            Assert.AreEqual(Direction.Down.ColumnOffset, _model!.Direction!.ColumnOffset);

        }

        [TestMethod]
        public void MoveUpTest()
        {
            MockandLoadText("20 20 5 10 6 10");

            _model!.ChangeDirection(Direction.Up);
            _model!.Move();

            Assert.AreEqual(Direction.Up.RowOffset, _model!.Direction!.RowOffset);
            Assert.AreEqual(Direction.Up.ColumnOffset, _model!.Direction!.ColumnOffset);
        }

        [TestMethod]
        public void InvalidTurnTest()
        {
            MockandLoadText("20 20 5 10 6 10");

            _model!.ChangeDirection(Direction.Right);

            Assert.AreEqual(0, _model.DirChanges.Count);

        }

        [TestMethod]
        public void MoreDirectionChanges()
        {
            MockandLoadText("20 20 5 10 6 10");

            _model!.ChangeDirection(Direction.Up);
            _model!.Move();
            Assert.AreEqual(Direction.Up.RowOffset, _model!.Direction!.RowOffset);
            Assert.AreEqual(Direction.Up.ColumnOffset, _model!.Direction!.ColumnOffset);

            _model!.ChangeDirection(Direction.Right);
            _model!.Move();
            Assert.AreEqual(Direction.Right.RowOffset, _model!.Direction!.RowOffset);
            Assert.AreEqual(Direction.Right.ColumnOffset, _model!.Direction!.ColumnOffset);

            _model!.ChangeDirection(Direction.Down);
            _model!.Move();
            Assert.AreEqual(Direction.Down.RowOffset, _model!.Direction!.RowOffset);
            Assert.AreEqual(Direction.Down.ColumnOffset, _model!.Direction!.ColumnOffset);

            _model!.ChangeDirection(Direction.Left);
            _model!.Move();
            Assert.AreEqual(Direction.Left.RowOffset, _model!.Direction!.RowOffset);
            Assert.AreEqual(Direction.Left.ColumnOffset, _model!.Direction!.ColumnOffset);

        }

        [TestMethod]
        public void SnakePositions()
        {
            MockandLoadText("20 20 5 10 6 10");

            Assert.AreEqual(5, _model!.SnakePositions.Count);

        }

        [TestMethod]
        public void ScoreTest()
        {
            MockandLoadText("20 20 5 10 6 10");

            Assert.AreEqual(0, _model!.Score);

        }

        [TestMethod]
        public void GameOverStep()
        {
            MockandLoadText("10 10");

            _model!.RestartGame();
            _model!.Move();
            _model!.Move();
            _model!.Move();
            _model!.Move();
            _model!.Move();


            Assert.AreEqual(true, _model!.IsGameOver);

        }

        [TestMethod]
        public void BarrierCollision()
        {
            MockandLoadText("10 10 5 8");

            _model!.RestartGame();
            _model!.Move();
            _model!.Move();
            _model!.Move();


            Assert.AreEqual(true, _model!.IsGameOver);

        }

        [TestMethod]
        public void CollisionWithSnakeBody()
        {
            MockandLoadText("10 10");

            _model!.RestartGame();

            _model?.Move();
            _model!.ChangeDirection(Direction.Up);
            _model?.Move();
            _model!.ChangeDirection(Direction.Left);
            _model?.Move();
            _model?.ChangeDirection(Direction.Down);
            _model?.Move();

            Assert.AreEqual(true, _model!.IsGameOver);

        }

        [TestMethod]
        public void EatFood()
        {
            MockandLoadText("10 10");

            _model!.RestartGame();

            _model!.Grid![5, 6] = GridValue.Food;

            _model!.Move();


            Assert.AreEqual(6, _model!.SnakePositions!.Count);
            Assert.AreEqual(1, _model!.Score);

        }

        [TestMethod]
        public void PauseTest()
        {
            MockandLoadText("10 10");

            Assert.AreEqual(false, _model!.IsRunning);

            _model!.IsRunning = true;

            Assert.AreEqual(true, _model.IsRunning);

            _model!.ManagePause();

            Assert.AreEqual(false, _model!.IsRunning);

        }

        [TestMethod]
        public void RestartGameTest1()
        {
            MockandLoadText("10 10");

            _model!.RestartGame();

            Assert.AreEqual(5, _model!.SnakePositions!.Count);
            Assert.AreEqual(0, _model!.Score);

        }

        [TestMethod]
        public void RestartGameTest2()
        {

            MockandLoadText("10 10");

            _model!.RestartGame();

            Assert.AreEqual(10, _model!.Rows);
            Assert.AreEqual(10, _model!.Cols);

        }

        [TestMethod]
        public void HeadPosition()
        {

            MockandLoadText("10 10");

            _model!.RestartGame();

            Assert.AreEqual(5, _model.HeadPosition().Row);
            Assert.AreEqual(5, _model!.HeadPosition().Column);

            Assert.AreEqual(5, _model.TailPosition().Row);
            Assert.AreEqual(1, _model!.TailPosition().Column);
        }

    }
}