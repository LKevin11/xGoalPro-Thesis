using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Snake.Model.Model
{
    /// <summary>
    /// Pozíció ostály
    /// </summary>
    public class Position
    {
        /// <summary>
        /// Sor koordináta
        /// </summary>
        public int Row { get; set; }
        /// <summary>
        /// Oszlop koordináta
        /// </summary>
        public int Column { get; set; }

        /// <summary>
        /// Konstruktor
        /// </summary>
        public Position(int row, int column)
        {
            Row = row;
            Column = column;
        }

        /// <summary>
        /// Adott pozícióból adott irányba elmozdítás
        /// </summary>
        /// <param name="direction">Irány</param>
        /// <returns></returns>
        public Position Translate(Direction direction)
        {
            return new Position(Row + direction.RowOffset, Column + direction.ColumnOffset);
        }

        public override bool Equals(object? obj)
        {
            return obj is Position position &&
                   Row == position.Row &&
                   Column == position.Column;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Row, Column);
        }

        public static bool operator ==(Position? left, Position? right)
        {
            return EqualityComparer<Position>.Default.Equals(left, right);
        }

        public static bool operator !=(Position? left, Position? right)
        {
            return !(left == right);
        }
    }
}
