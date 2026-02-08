using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MineSweeper.Persistence
{
    public interface IFileManager
    {
        /// <summary>
        /// Saves data
        /// </summary>
        /// <param name="data">Output data</param>
        /// <returns>true if save was successful else false</returns>
        bool SaveFile(OutputData data);

    }

    
    public struct OutputData
    {
        public string fileName;
        public string time;
        public string score;

        public OutputData(string fileName, string time, string score)
        {
            this.fileName = fileName;
            this.time = time;
            this.score = score;
        }

    }

}
