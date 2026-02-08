using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static System.Formats.Asn1.AsnWriter;

namespace MineSweeper.Persistence
{

    public class TextFileManager : IFileManager
    {

        public TextFileManager() { }

        /// <summary>
        /// Saves data to txt
        /// </summary>
        /// <param name="data">Output data</param>
        /// <returns>true if save was successful else false</returns>
        public bool SaveFile(OutputData data)
        {

            try
            {
                using (StreamWriter writer = new StreamWriter(data.fileName, false))
                {
                    writer.WriteLine("Filename: " + data.fileName);
                    writer.WriteLine("Date: " + data.time);
                    writer.WriteLine("Score: " + data.score + " s");
                    writer.WriteLine();
                }

                return true;
            }
            catch (Exception ex)
            {
                ex.ToString();
                return false;
            }


        }

    }
}
