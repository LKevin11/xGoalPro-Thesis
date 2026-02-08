using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Snake.Model.Persistence
{
    /// <summary>
    /// Snake adatelérés kivétel típusa.
    /// </summary>
    public class FileManagerException : Exception
    {
        /// <summary>
        /// Snake adatelérés kivétel típusának példányosítása.
        /// </summary>
        public FileManagerException(string message) : base(message) { }

        public FileManagerException(string message, Exception innerException) : base(message, innerException) { }


    }
}
