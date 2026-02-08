using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Snake.Model.Model;

namespace Snake.Model.Persistence
{

    /// <summary>
    /// Txt fájl betöltése
    /// </summary>
    public class TextFileManager : IFileManager
    {
        /// <summary>
        /// Init
        /// </summary>
        public TextFileManager() { }


        /// <summary>
        /// Betöltés metódúsa
        /// </summary>
        /// <param name="size">Pálya mérete</param>
        /// <returns>Stringben az adatok</returns>
        /// <exception cref="FileManagerException"></exception>
        public string? Load(GameFieldSize size)
        {
            try
            {
                string? path = null;


                if (size == GameFieldSize.SMALL)
                {
                    path = $"{Directory.GetParent(Environment.CurrentDirectory)?.Parent?.Parent?.FullName}\\Input\\small.txt";
                    return "15 15 1 2 5 6";
                }

                if (size == GameFieldSize.MEDIUM)
                {
                    path = $"{Directory.GetParent(Environment.CurrentDirectory)?.Parent?.Parent?.FullName}\\Input\\medium.txt";
                    //return File.ReadAllText(path);
                    return "20 20 15 15 5 5 12 4";
                }

                if (size == GameFieldSize.LARGE)
                {
                    path = $"{Directory.GetParent(Environment.CurrentDirectory)?.Parent?.Parent?.FullName}\\Input\\large.txt";
                    return "25 25 20 20";
                }

                return null;
            }
            catch (Exception ex)
            {
                throw new FileManagerException(ex.Message, ex);
            }
        }

    }
}
