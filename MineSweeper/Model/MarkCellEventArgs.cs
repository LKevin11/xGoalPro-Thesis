using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MineSweeper.Model
{
    public class MarkCellEventArgs : EventArgs
    {

        public Int32 Row { get; set; }
        public Int32 Column { get; set; }
        public Boolean Flag {  get; set; }

        public MarkCellEventArgs(Int32 row, Int32 column, Boolean flag) { Row = row; Column = column; Flag = flag; }
        

    }
}
