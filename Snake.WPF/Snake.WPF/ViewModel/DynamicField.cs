using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Snake.Model.Model;

namespace Snake.WPF.ViewModel
{
    /// <summary>
    /// Dinamikus mező osztálya
    /// </summary>
    public class DynamicField : ViewModelBase
    {
        /// <summary>
        /// Mező érték
        /// </summary>
        private int _value;

        /// <summary>
        /// Sor koordináta
        /// </summary>
        public int X {  get; set; }
        /// <summary>
        /// Oszlop koordináta
        /// </summary>
        public int Y { get; set; }
        public int Value { get { return _value; } set { _value = value; OnPropertyChanged(nameof(Value)); } }

        public DynamicField(int x, int y, int v)
        {
            X = x;
            Y = y;
            _value = v;
        }




    }
}
