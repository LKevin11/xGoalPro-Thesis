using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MineSweeper.Model
{
    /// <summary>
    /// MineSweeper field
    /// </summary>
    public class Cell
    {

        /// <summary>
        /// Gamefield constructor
        /// </summary>
        public Cell()
        {
            HasMine = false;
            IsRevealed = false;
            AdjacentMines = 0;
            IsMarked = false;
        }

        /// <summary>
        /// Is field mine
        /// </summary>
        public bool HasMine {  get; set; }
        /// <summary>
        /// Gamefield visibility
        /// </summary>
        public bool IsRevealed { get; set; }
        /// <summary>
        /// Number of adjacent mines
        /// </summary>
        public int AdjacentMines {  get; set; }
        /// <summary>
        /// Is field marked
        /// </summary>
        public bool IsMarked { get; set; }

    }
}
