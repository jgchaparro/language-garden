import sqlite3
import pandas as pd

class TextAdder:
    """
    Manages the addition of texts to the database.
    """
    def __init__(self, 
                 db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def main(self,
             text_df: pd.DataFrame,
             url: str,
             author: str = 'Unknown',
             year: int = -1,
             variety_id: int = 0,
             replace: bool = False):
        """
        Adds a source and text to the database.
        """
        # If replace is activated and the source already exists, delete it along with its texts
        source_query = self.query(f"SELECT * FROM sources WHERE url = '{url}' LIMIT 1;")
        source_exists = source_query is not None
        if replace and source_exists:
            source_id = source_query['source_id'].values[0]
            self.delete_source_and_texts(source_id)
            print(f"Source with ID {source_id} deleted.")

        # Add source
        self.add_source(url, author, year, variety_id)

        # Add text
        self.add_text(text_df, self.source_id)

    def delete_source_and_texts(self,
                                source_id: 1):
        """
        Deletes a source and its texts from the database.
        """
        delete_texts_query = f"""
        DELETE FROM texts
        WHERE source_id = '{source_id}'"""
        self.query(delete_texts_query)

        delete_source_query = f"""
        DELETE FROM sources
        WHERE source_id = '{source_id}';"""
        self.query(delete_source_query)
            
        print(f"Source with ID {source_id} deleted.")

    def add_source(self, 
                   url: str,
                   author: str,
                   year: int,
                   variety_id: int,
                   replace: bool = False):
        """
        Appends a new source to the database.
        """
        # Check if the source already exists
        query = f"""
        SELECT * FROM sources
        WHERE url = '{url}'
        LIMIT 1;
        """
        source_exists = self.query(query)
        if source_exists is not None:
            print("Source already exists.")
            raise ValueError("Source already exists. Please, use the 'replace' parameter to update the source.")
    
        # Replace source if it already exists
        if replace and source_exists:
            source_id = source_exists['source_id'].values[0]
            self.delete_source_and_texts(source_id)
            print(f"Source with ID {source_id} deleted.")
        
        # Compute source name from URL
        # TODO: generalize when using other sources
        source_name = self.url_to_filename(url)

        # Build dataframe with source information
        source_df = pd.DataFrame({
            'name' : [source_name],
            'url' : [url],
            'author' : [author],
            'year' : [year],
            'variety_id' : [variety_id]
        })

        # Add to database
        source_df.to_sql('sources', self.conn, if_exists = 'append', index = False)

        # Get the source ID
        query = f"""
        SELECT source_id FROM sources
        WHERE url = '{url}'
        LIMIT 1;
        """
        self.source_id = self.query(query)['source_id'].values[0]

        print(f"Source '{source_name}' with ID {self.source_id} added to the database.")

    def add_text(self, 
                 text_df: pd.DataFrame, 
                 origin: str,
                 source_id: int = None):
        """
        Appends a new sentence batch to the database.
        """
        # Set source ID
        if not source_id:
            source_id = self.source_id
        
        # Check that there are no texts from the same source
        query = f"""
        SELECT * FROM texts
        WHERE source_id = '{origin}'
        LIMIT 1;
        """
        text_exists = self.query(query)
        if text_exists:
            print("Text already exists.")
            raise ValueError("Text already exists. Please, use the 'replace' parameter to update the text.")
        
        # Extract maximum text ID
        query = f"""
        SELECT MAX(text_id) FROM texts;
        """
        max_text_id = self.query(query).values[0][0]

        # Format
        temp_df = text_df.copy()
        temp_df['source_id'] = origin
        temp_df['text_id'] = range(max_text_id + 1, max_text_id + 1 + len(temp_df))

        # Push to database
        temp_df.to_sql('texts', self.conn, if_exists = 'append', index = False)

        print(f"Text from '{origin}' added to the database.")         
    
    def query(self, 
              query: str):
        """
        Auxiliary method to execute a query and return the results as a DataFrame.
        """
        self.cursor.execute(query)
        fetched = self.cursor.fetchall()

        if len(fetched) > 0:
            temp_df = pd.DataFrame(fetched, columns=[i[0] for i in self.cursor.description])
            return temp_df
        else:
            print('Query executed successfully. No results to show.')

    def url_to_filename(self, url: str):
        """
        Converts a url to a filename.
        """
        filename_base = url.replace("https://", "").strip('/').replace("/", "_")
        return filename_base