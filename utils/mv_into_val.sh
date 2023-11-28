SRC=$1  # путь к корню датасета
TYPE=$2  # GameEngineData или DownscaleData
FOLDER=$3  # название проекта = название папки
DST=$4  # папка куда сохранять данные
TESTSIZE=$5  # размер тестовой части
EXT=$6  # расширение файлов

cp -r "$SRC"/"$TYPE"/"$FOLDER"/ .
python mv_into_val.py --folder "$FOLDER" --test-size "$TESTSIZE"

cd "$FOLDER"/270p
tar -czvf train-270p.tar.gz *."$EXT"
mv train-270p.tar.gz ../..
cd ../..

cd "$FOLDER"/360p
tar -czvf train-360p.tar.gz *."$EXT"
mv train-360p.tar.gz ../..
cd ../..

cd "$FOLDER"/540p
tar -czvf train-540p.tar.gz *."$EXT"
mv train-540p.tar.gz ../..
cd ../..

cd "$FOLDER"/1080p
tar -czvf train-1080p.tar.gz *."$EXT"
mv train-1080p.tar.gz ../..
cd ../..

cd "$FOLDER"\_val/270p
tar -czvf val-270p.tar.gz *."$EXT"
mv val-270p.tar.gz ../..
cd ../..

cd "$FOLDER"\_val/360p
tar -czvf val-360p.tar.gz *."$EXT"
mv val-360p.tar.gz ../..
cd ../..

cd "$FOLDER"\_val/540p
tar -czvf val-540p.tar.gz *."$EXT"
mv val-540p.tar.gz ../..
cd ../..

cd "$FOLDER"\_val/1080p
tar -czvf val-1080p.tar.gz *."$EXT"
mv val-1080p.tar.gz ../..
cd ../..

rm -rf "$FOLDER"
rm -rf "$FOLDER"\_val

mkdir -p "$DST"/"$TYPE"/"$FOLDER"
mv *.tar.gz "$DST"/"$TYPE"/"$FOLDER"