using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Snake.Model.Model
{
    public class GameLoopEventArgs : EventArgs
    {
        /// <summary>
        /// Időzítő eseményargumentum osztálya, tartalmazza, hogy fut-e még az időzítő
        /// </summary>
        public bool IsRunning { get; set; }

        public GameLoopEventArgs(bool isRunning)
        {
            this.IsRunning = isRunning;
        }

    }
}
