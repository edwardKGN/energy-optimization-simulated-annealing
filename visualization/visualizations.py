import numpy as np
import matplotlib.pyplot as plt

def configure_stream_visualization(StreamDataObject, shift_array):
    enthalpies_dict = {}

    for row in np.arange(len(StreamDataObject.get_pd_prod_plan())):
        prod_plan_dict = StreamDataObject.PRISM(row=row)

        for index, stream in enumerate(prod_plan_dict):
            if row == 0:
                enthalpies_dict[stream] = StreamDataObject.single_stream_builder(grade=prod_plan_dict[stream]['grade'],
                                                                                           stream_shift=shift_array[row][index])
            else:
                enthalpies_dict[stream] += StreamDataObject.single_stream_builder(grade=prod_plan_dict[stream]['grade'],
                                                                                            stream_shift=shift_array[row][index])
    
    return enthalpies_dict

def visualize_stream_energy(stream_name, num_time_blocks, stream_energy, figure_num):  # Only configures the figure
    plt.plot(np.arange(num_time_blocks), stream_energy, label=stream_name)

    plt.legend()
    plt.figure(figure_num)
    plt.xlabel('Time Blocks')
    plt.ylabel('Energy')