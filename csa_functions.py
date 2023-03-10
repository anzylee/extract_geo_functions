import os
import simpledbf
import arcpy
import _thread
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# This script is from F:\tuflow-SC\py_modules

def csa_functions(path_xsect, interval, path_terrains, ini_water_depth, min_elev, max_slope,
                           int_len_depth_method, Execute_StackProfile_3d, figure_xsect, unit, method, method_param):
    # This python module calculates the flow discharge using the water depth at a certain cross-section
    # The required inputs are:
    #   path_up_xsect         - path to the transect line (XX.shp, shape file)
    #   path_terrain            - path to the terraian (XX.asc)
    #   water_depth             - the water depth at the xsect of interested (e.g. 1st riffle-crest)
    #   Execute_StackProfile_3d - 1 if you need to generate xsect profile in xlsx
    #   figure_xsect            - 1 if you want to see the xsect profile and water stage

    width_series = []

    # path to upstream xsect shp file
    xsectshp1 = path_xsect

    print(xsectshp1)

    # Load Raster DEM
    #terrain = path_terrain

    # Define projection
    dsc = arcpy.Describe(xsectshp1)
    coord_sys = dsc.spatialReference
    #arcpy.DefineProjection_management(terrain, coord_sys)

    terrain_num = 0

    if len(path_terrains) == 2:
        for terrain in path_terrains:
            # Stack Profile
            xsecttab = '../samples/xsect_table'+str(terrain_num)+'.dbf'
            print(xsecttab)

            if os.path.isfile(xsecttab):
                os.remove(xsecttab)

            # Execute Stack Profile
            arcpy.CheckOutExtension("3D")
            arcpy.StackProfile_3d(xsectshp1, profile_targets=[terrain], out_table=xsecttab)
            if terrain_num == 0: # pre-fire
                xsectdbf0 = simpledbf.Dbf5(xsecttab)
                xsectdfst0 = xsectdbf0.to_dataframe()
                xsectdf0 = xsectdfst0
            elif terrain_num == 1: # post-fire
                xsectdbf1 = simpledbf.Dbf5(xsecttab)
                xsectdfst1 = xsectdbf1.to_dataframe()
                xsectdf1 = xsectdfst1

            #Line_IDs = range(0, max(xsectdf1['LINE_ID'])+1)
            Line_IDs = xsectdf0['LINE_ID'].unique()
            terrain_num += 1

        bed_stage_width_df = pd.DataFrame(np.zeros((max(Line_IDs), len(path_terrains)+3)))

        for Line_ID in Line_IDs:
            print("Line ID = ", str(Line_ID), ' (or '+str(Line_ID)+' in figure)')

            x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                          min_elev,
                                                                                          max_slope, ini_water_depth)
            x1, z1, width1, min_elevation1, water_stage1, x_intercept1 = width_calculator(xsectdf1, Line_ID,
                                                                                          min_elev,
                                                                                          max_slope, ini_water_depth)

            if method in ['same_vertical_offset']:

                if figure_xsect == 1:
                    # Figure, at the first riffle-crest
                    plt.figure(1)
                    plt.plot(x0, z0, '-', label='pre-fire')
                    plt.plot([np.min(x0), np.max(x0)], [water_stage0, water_stage0])
                    plt.plot(x_intercept0, water_stage0 * np.ones(len(x_intercept0)), '*')
                    plt.plot(x1, z1, '--', label='post-fire')
                    plt.plot([np.min(x1), np.max(x1)], [water_stage1, water_stage1])
                    plt.plot(x_intercept1, water_stage1 * np.ones(len(x_intercept1)), '*')
                    # plt.plot(xi1, water_stage, 'r*')
                    # plt.plot(xi2, water_stage, 'r*')

                    plt.grid()
                    plt.legend()
                    plt.xlabel('Lateral Distance ' + '(' + unit + ')')
                    plt.ylabel('Elevation ' + '(' + unit + ')')
                    plt.title('Cross-sectional profile')
                    # plt.show()
                    path_fig = './figures/xsect_' + int_len_depth_method
                    if not os.path.exists(path_fig):
                        os.mkdir(path_fig)

            elif method in ['same_water_stage']:

                if water_stage0 > water_stage1:
                    modi_water_depth = water_stage0 - min_elevation1

                    x1, z1, width1, min_elevation1, water_stage1, x_intercept1 = width_calculator(xsectdf1, Line_ID,
                                                                                                  min_elev,
                                                                                                  max_slope,
                                                                                                  modi_water_depth)
                elif water_stage1 > water_stage0:
                    modi_water_depth = water_stage1 - min_elevation0
                    x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                                  min_elev,
                                                                                                  max_slope,
                                                                                                  modi_water_depth)
                if figure_xsect == 1:
                    # Figure, at the first riffle-crest
                    plt.figure(1)
                    plt.plot(x0, z0, '-', label='pre-fire')
                    plt.plot([np.min(x0), np.max(x0)], [water_stage0, water_stage0])
                    plt.plot(x_intercept0, water_stage0 * np.ones(len(x_intercept0)), '*')
                    plt.plot(x1, z1, '--', label='post-fire')
                    plt.plot([np.min(x1), np.max(x1)], [water_stage1, water_stage1])
                    plt.plot(x_intercept1, water_stage1 * np.ones(len(x_intercept1)), '*')
                    # plt.plot(xi1, water_stage, 'r*')
                    # plt.plot(xi2, water_stage, 'r*')

                    plt.grid()
                    plt.legend()
                    plt.xlabel('Lateral Distance ' + '(' + unit + ')')
                    plt.ylabel('Elevation ' + '(' + unit + ')')
                    plt.title('Cross-sectional profile')
                    # plt.show()
                    path_fig = './figures/xsect_' + int_len_depth_method
                    if not os.path.exists(path_fig):
                        os.mkdir(path_fig)


            #width_series = np.append(width_series, width)
            bed_stage_width_df.loc[max(Line_IDs) - Line_ID, 0] = min_elevation0
            bed_stage_width_df.loc[max(Line_IDs) - Line_ID, 1] = min_elevation1
            bed_stage_width_df.loc[max(Line_IDs) - Line_ID, 2] = water_stage0
            bed_stage_width_df.loc[max(Line_IDs) - Line_ID, 3] = width0
            bed_stage_width_df.loc[max(Line_IDs) - Line_ID, 4] = width1

            if figure_xsect == 1:
                plt.savefig(path_fig + '/profile_' + str(Line_ID))
                plt.close() # # #

    else:
        for terrain in path_terrains:
            print('terrain = '+os.path.abspath(terrain))
            # Stack Profile
            xsecttab = os.path.dirname(terrain)+'/xsect_table'+str(terrain_num)+'.dbf'
            print(os.path.abspath(xsecttab))

            if os.path.isfile(xsecttab):
                os.remove(xsecttab)

            # Execute Stack Profile
            arcpy.CheckOutExtension("3D")
            arcpy.StackProfile_3d(xsectshp1, profile_targets=[terrain], out_table=xsecttab)

            xsectdbf0 = simpledbf.Dbf5(xsecttab)
            xsectdfst0 = xsectdbf0.to_dataframe()
            xsectdf0 = xsectdfst0

            #Line_IDs = range(0, max(xsectdf1['LINE_ID'])+1)
            Line_IDs = xsectdf0['LINE_ID'].unique()
            print(Line_IDs)

        bed_stage_width_df = pd.DataFrame(np.zeros((max(Line_IDs), len(path_terrains)+3)))

        for Line_ID in Line_IDs:
            print("Line ID = ", str(Line_ID), ' (or ' + str(Line_ID) + ' in figure)')
            #Line_IDs = Line_IDs[::-1]
            #print(Line_IDs)

            if method in ['const_slope']:

                x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                              min_elev,
                                                                                              max_slope, ini_water_depth)

                if Line_ID == min(Line_IDs):
                    min_elevation_y0 = min_elevation0
                z_const_slope = method_param[0]*(Line_ID)*interval + (min_elevation_y0 + method_param[1])
                modi_water_depth = z_const_slope - min_elevation0
                print(z_const_slope)
                print(min_elevation0)
                print(modi_water_depth)

                x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                              min_elev,
                                                                                              max_slope, modi_water_depth)

            elif method in ['vertical_offset']:

                x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                              min_elev,
                                                                                              max_slope, ini_water_depth)

                if Line_ID == min(Line_IDs):
                    min_elevation_y0 = min_elevation0
                print(min_elevation0)

            elif method in ['max_width_diff']:

                d_water_depth = 0.01
                water_depth = d_water_depth
                water_depths, widths = [], []
                x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                              min_elev,
                                                                                              max_slope, water_depth)

                while len(x_intercept0) > 1:
                    x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                                  min_elev,
                                                                                                  max_slope, water_depth)


                    water_depths = np.append(water_depths, water_depth)
                    widths = np.append(widths, width0)

                    water_depth = water_depth + d_water_depth

                widths = widths[:-5]
                water_depths = water_depths[:-5]

                plt.figure(10)
                plt.plot(water_depths, widths, 'k.')

                if len(method_param) == 1:
                    if method_param > 0:
                        scaling_w = 5.44 * pow(method_param, 0.477)
                        lower_b = 0.5 * scaling_w
                        upper_b = 2 * scaling_w

                        ind_bounds = (widths>lower_b)*(widths<upper_b)
                        widths = widths[ind_bounds]
                        water_depths = water_depths[ind_bounds]

                    else:
                        lower_b = 0
                        upper_b = 0
                elif len(method_param) == 2:
                    lower_b = method_param[0]
                    upper_b = method_param[1]

                    ind_bounds = (widths > lower_b) * (widths < upper_b)
                    widths = widths[ind_bounds]
                    water_depths = water_depths[ind_bounds]

                widths_diff = np.diff(widths)
                plt.figure(11)
                plt.plot(water_depths[:-1], widths_diff, 'k.')

                plt.figure(10)
                plt.plot(water_depths, widths, 'b.')
                #if lower_b > 0:
                #    plt.plot([lower_b, lower_b], [min(widths_diff), max(widths_diff)], 'k--')
                #    plt.plot([upper_b, upper_b], [min(widths_diff), max(widths_diff)], 'k--')
                plt.grid()
                plt.xlabel('Water depth (m)')
                plt.ylabel('Width (m)')

                path_fig = os.path.dirname(terrain) + '/XS/width_' + int_len_depth_method
                if not os.path.exists(os.path.dirname(path_fig)):
                    os.mkdir(os.path.dirname(path_fig))
                if not os.path.exists(path_fig):
                    os.mkdir(path_fig)
                plt.savefig(path_fig + '/width_' + str(Line_ID))
                plt.close()

                plt.figure(11)
                plt.plot(water_depths[:-1], widths_diff, '.')

                plt.grid()
                plt.xlabel('Water depth (m)')
                plt.ylabel('Width difference (m/0.01m)')

                path_fig = os.path.dirname(terrain) + '/XS/width_diff_' + int_len_depth_method
                if not os.path.exists(os.path.dirname(path_fig)):
                    os.mkdir(os.path.dirname(path_fig))
                if not os.path.exists(path_fig):
                    os.mkdir(path_fig)
                plt.savefig(path_fig + '/width_diff_' + str(Line_ID))
                plt.close()

                widths_diff_ind = np.where(widths_diff == max(widths_diff))
                water_depth = water_depths[widths_diff_ind[0][0]]

                x0, z0, width0, min_elevation0, water_stage0, x_intercept0 = width_calculator(xsectdf0, Line_ID,
                                                                                              min_elev,
                                                                                              max_slope, water_depth)
                print("Width = ", width0, "Lower/upper bounds = (", lower_b, ",", upper_b, ")")

            else:
                print("Enter a valid method name")


            plt.figure(1)
            plt.plot(x0, z0, '-')
            plt.plot([np.min(x0), np.max(x0)], [water_stage0, water_stage0])
            plt.plot(x_intercept0, water_stage0 * np.ones(len(x_intercept0)), '*')
            # plt.plot(xi1, water_stage, 'r*')
            # plt.plot(xi2, water_stage, 'r*')

            plt.grid()
            #plt.legend()
            plt.xlabel('Lateral Distance ' + '(' + unit + ')')
            plt.ylabel('Elevation ' + '(' + unit + ')')
            plt.title('Cross-sectional profile')
            # plt.show()
            path_fig = os.path.dirname(terrain) + '/XS/xsect_' + int_len_depth_method
            if not os.path.exists(os.path.dirname(path_fig)):
                os.mkdir(os.path.dirname(path_fig))
            if not os.path.exists(path_fig):
                os.mkdir(path_fig)
            plt.savefig(path_fig + '/profile_' + str(Line_ID))
            plt.close()

            #width_series = np.append(width_series, width)
            # worked for SFE 322
            bed_stage_width_df.loc[Line_ID, 0] = min_elevation0
            bed_stage_width_df.loc[Line_ID, 1] = water_stage0
            bed_stage_width_df.loc[Line_ID, 2] = width0

            '''
            bed_stage_width_df.loc[Line_ID, 0] = min_elevation0
            bed_stage_width_df.loc[Line_ID, 1] = water_stage0
            bed_stage_width_df.loc[Line_ID, 2] = width0
            '''

    return Line_IDs, bed_stage_width_df



def width_calculator(xsectdf1, Line_ID, min_elev, max_slope, water_depth):
    # Construct a functional relationship between A and h
    x = np.array(xsectdf1.loc[xsectdf1['LINE_ID'] == Line_ID]['FIRST_DIST'])
    z = np.array(xsectdf1.loc[xsectdf1['LINE_ID'] == Line_ID]['FIRST_Z'])

    ind_nan = np.where(z < min_elev)  # z == -9999
    x = np.delete(x, ind_nan)
    z = np.delete(z, ind_nan)

    slope = np.diff(z)/np.diff(x)
    ind_diff = np.where(slope > max_slope)

    if len(ind_diff[0]) > 0:
        x = np.delete(x, ind_diff[0])
        z = np.delete(z, ind_diff[0])
        if ind_diff[0][0] > 0:
            x = np.delete(x, range(ind_diff[0][0])) # delete the left part of the profile as well
            z = np.delete(z, range(ind_diff[0][0]))

    slope = np.diff(z) / np.diff(x)
    ind_diff = np.where(slope < -max_slope)

    if len(ind_diff[0]) > 0:
        x = np.delete(x, ind_diff[0] + 1)
        z = np.delete(z, ind_diff[0] + 1)

    xvals = np.arange(min(x), max(x), 0.1)
    zinterp = np.interp(xvals, x, z)

    x = xvals
    z = zinterp

    min_elevation = min(z)  # np.sort(z)[1]

    water_stage = min_elevation + water_depth

    z0 = z - water_stage
    # print(z0)
    ind = []
    x_intercept = []

    # Calculate Width

    for ii in range(0, z.__len__() - 1):
        if np.sign(z0[ii] * z0[ii + 1]) < 0.01:
            ind.append(ii)

    width = 0

    #print(ind)
    '''
    ## width = distance between the first & last intersect w/ water stage
    for ii in range(0, ind.__len__()):
        if len(ind) > 1:

            m1 = (z0[ind[ii]] - z0[ind[ii] + 1]) / (x[ind[ii]] - x[ind[ii] + 1])
            xi1 = (-z0[ind[ii]] + m1 * x[ind[ii]]) / m1

            x_intercept = np.append(x_intercept, xi1)

            width = x_intercept[-1] - x_intercept[0]

        else:
            width = 0
    '''
    '''
    ## width = summation of distances between the intersect w/ water stage
    for ii in range(0, ind.__len__(), 2):
        if len(ind) > 1:

            m1 = (z0[ind[ii]] - z0[ind[ii] + 1]) / (x[ind[ii]] - x[ind[ii] + 1])
            xi1 = (-z0[ind[ii]] + m1 * x[ind[ii]]) / m1

            m2 = (z0[ind[ii+1]] - z0[ind[ii+1] + 1]) / (x[ind[ii+1]] - x[ind[ii+1] + 1])
            xi2 = (-z0[ind[ii+1]] + m2 * x[ind[ii+1]]) / m2

            dx = xi2 - xi1

            width = width + dx

            x_intercept = np.append(x_intercept, xi1)
            x_intercept = np.append(x_intercept, xi2)

        else:
            width = 0
    '''

    ## width = maximum segment distance
    dx_pre = 0

    if len(ind) > 1 and np.mod(len(ind), 2) == 1: # if the number of intercept is odd
        # ind = np.append(ind, ind[-1]+1)
        ii = 0
        if (z0[ind[ii]] - z0[ind[ii] + 1]) / (x[ind[ii]] - x[ind[ii] + 1]) > 0:
            ind = ind[1:]  # if the slope of the first intercept is positive, remove the first intercept
        else:
            ind = ind[:-1]

    for ii in range(0, ind.__len__(), 2):
        if len(ind) > 1:
            m1 = (z0[ind[ii]] - z0[ind[ii] + 1]) / (x[ind[ii]] - x[ind[ii] + 1])
            xi1 = (-z0[ind[ii]] + m1 * x[ind[ii]]) / m1

            m2 = (z0[ind[ii+1]] - z0[ind[ii+1] + 1]) / (x[ind[ii+1]] - x[ind[ii+1] + 1])
            xi2 = (-z0[ind[ii+1]] + m2 * x[ind[ii+1]]) / m2

            dx = xi2 - xi1

            #width = width + dx
            if dx > dx_pre:
                width = dx
            else:
                width = dx_pre

            x_intercept = np.append(x_intercept, xi1)
            x_intercept = np.append(x_intercept, xi2)


        else:
            width = 0

    return x, z, width, min_elevation, water_stage, x_intercept