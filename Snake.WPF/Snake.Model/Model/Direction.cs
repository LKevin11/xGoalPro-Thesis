using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Snake.Model.Model
{
    public class Direction
    {

        //statikus irányok, beállítások
        public readonly static Direction Left = new Direction(0,-1);
        public readonly static Direction Right = new Direction(0, 1);
        public readonly static Direction Up = new Direction(-1, 0);
        public readonly static Direction Down = new Direction(1, 0);

        /// <summary>
        /// Sor konstans
        /// </summary>
        public int RowOffset { get; set; }
        /// <summary>
        /// Oszlop konstans
        /// </summary>
        public int ColumnOffset { get; set; }

        /// <summary>
        /// Konstruktor
        /// </summary>
        private Direction(int rowOffset, int columnOffset)
        {
            RowOffset = rowOffset;
            ColumnOffset = columnOffset;
        }

        /// <summary>
        /// Irány ellenttetje
        /// </summary>
        /// <returns>Irány</returns>
        public Direction Opposite()
        {
            return new Direction(-RowOffset, -ColumnOffset);
        }

        public override bool Equals(object? obj)
        {
            return obj is Direction direction &&
                   RowOffset == direction.RowOffset &&
                   ColumnOffset == direction.ColumnOffset;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(RowOffset, ColumnOffset);
        }

        public static bool operator ==(Direction? left, Direction? right)
        {
            return EqualityComparer<Direction>.Default.Equals(left, right);
        }

        public static bool operator !=(Direction? left, Direction? right)
        {
            return !(left == right);
        }
    }
}
