using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Snake.Model.Model;

namespace Snake.Model.Persistence
{
    /// <summary>
    /// Snake fájkezelő felülete.
    /// </summary>
    public interface IFileManager
    {

        /// <summary>
        /// Játék betöltése.
        /// </summary>
        string? Load(GameFieldSize size);

    }
}
