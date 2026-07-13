import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import csv

class PlotUtils:

    @staticmethod
    def _fig2data (fig):
        """
        @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
        @param fig a matplotlib figure
        @return a numpy 3D array of RGBA values
        """
        # draw the renderer
        fig.canvas.draw ( )
 
        # Get the RGBA buffer from the figure
        w,h = fig.canvas.get_width_height()
        
        #print("w ", w, " h ", h)
        
        buf = np.fromstring ( fig.canvas.tostring_argb(), dtype=np.uint8 )
        buf.shape = ( w, h,4 )
 
        # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
        buf = np.roll ( buf, 3, axis = 2 )
        return buf    

    @staticmethod
    def _fig2img (fig):
        """
        @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
        @param fig a matplotlib figure
        @return a Python Imaging Library ( PIL ) image
        """
        # put the figure pixmap into a numpy array
        buf = PlotUtils._fig2data ( fig )
        w, h, d = buf.shape
        
        return Image.frombuffer( "RGBA", ( w ,h ), buf.tostring( ) )
    
    @staticmethod
    def create_plot_anim(x_values, y_values, labels, image_xinch, image_yinch):
        
        plot_images = []
        plot_image_count = x_values.shape[0]
        
        min_x = np.min(x_values)
        max_x = np.max(x_values)
        min_y = np.min(y_values)
        max_y = np.max(y_values)
        
        for i in range(plot_image_count):
            fig, ax = plt.subplots(figsize=(image_xinch,image_yinch))
            for j in range(y_values.shape[0]):
                ax.plot(x_values[:i], y_values[j, :i], label=labels[j])
            ax.set_xlim(min_x, max_x)
            ax.set_ylim(min_y, max_y)
            ax.legend(bbox_to_anchor=(-0.05, 1.0))
            
            fig.show()
    
            plot_image = PlotUtils._fig2img( fig )
            
            plot_images.append(plot_image)
    
            plt.close()
            
        return plot_images
    
    @staticmethod
    def save_data_as_csv(values, labels, csv_file_name):
        with open(csv_file_name, 'w') as csv_file:
            csv_columns = list(labels)
            csv_col_count = values.shape[0]
            csv_row_count = values.shape[1]
            
            csv_writer = csv.DictWriter(csv_file, fieldnames=csv_columns, delimiter=',', lineterminator='\n')
            csv_writer.writeheader()
    
            for row in range(csv_row_count):
        
                csv_row = {}
        
                for col in range(csv_col_count):
                    csv_row[labels[col]] = values[col][row]

                csv_writer.writerow(csv_row)
    
    @staticmethod
    def save_loss_as_csv(loss_history, csv_file_name):
        with open(csv_file_name, 'w') as csv_file:
            csv_columns = list(loss_history.keys())
            csv_row_count = len(loss_history[csv_columns[0]])
            
            
            csv_writer = csv.DictWriter(csv_file, fieldnames=csv_columns, delimiter=',', lineterminator='\n')
            csv_writer.writeheader()
        
            for row in range(csv_row_count):
            
                csv_row = {}
            
                for key in loss_history.keys():
                    csv_row[key] = loss_history[key][row]
    
                csv_writer.writerow(csv_row)
    
    @staticmethod
    def save_loss_as_image(loss_history, image_file_name):
        keys = list(loss_history.keys())
        epochs = len(loss_history[keys[0]])
        
        for key in keys:
            plt.plot(range(epochs), loss_history[key], label=key)
            
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()
        plt.show()
        plt.savefig(image_file_name)