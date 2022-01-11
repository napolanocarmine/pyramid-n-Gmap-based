# default_exp pixelmap
# > Pixelmaps have custom construction and will take more care of what i-cells are allowed to be contracted/removed.

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


#export

import logging
import numpy as np
from combinatorial.notebooks.combinatorial.gmaps import nGmap
from combinatorial.notebooks.combinatorial.zoo import G2_SQUARE_BOUNDED, G2_SQUARE_UNBOUNDED

import matplotlib.pyplot as plt


from pixel_map_z_curve_full import D, alpha_0, R, C
from custom_dict_gmap import dict_nGmap



#-------------------------------- PixelMap class ----------------------------------------
class PixelMap (nGmap):
    """2-gMap representing an RxC image grid"""

    @property
    def n_rows (self):
        return self._nR

    @property
    def n_cols (self):
        return self._nC

    # vertex coordinates for the 8 darts in one pixel
    vertices = np.fromstring("""\
    0 0 1 0 2 0 2 1 2 2 1 2 0 2 0 1
    """, sep=' ', dtype=np.float32).reshape(8, 2)
    vertices -= 1
    vertices *= .95
    vertices += 1
    vertices /= 2
    vertices -= .5

    # text offsets relative to darts
    text_offsets = np.fromstring("""\
    0 0 -1 -1   0  0 1 1
    1 1  0  0  -1 -1 0 0
    """, sep=" ").reshape(2, 8).T

    text_angles = [0,0,-90,-90,0,0,-90,-90]
    text_HAs = 'center center right right center center left left'.split()
    text_VAs = 'top top center center bottom bottom center center'.split()

    def _plot_dart_no (self, dart, rotate = False):
        if dart >= 8*self.n_rows*self.n_cols:
            return #  TODO plot the boundary darts, too, if the maps is unbounded
        vi0, vi1 = dart % 8, 1 + dart % 8
        if vi1 == 8:
            vi1 = 0
        verts = PixelMap.vertices [[vi0,vi1]]
        verts += [(dart // 8) %  self.n_cols, (dart // 8) // self.n_cols]
        mid = .5 * verts[0] + .5 * verts[1]
        mid += 0.005 * PixelMap.text_offsets [vi0]
        plt.text (mid[0],mid[1],dart,
            ha      = PixelMap.text_HAs  [dart%8],
            va      = PixelMap.text_VAs   [dart%8],
            rotation= PixelMap.text_angles[dart%8] * rotate
        )

    def plot_faces (self, number_darts = True):
        vertices = PixelMap.vertices
        # iterate over 2-cells
        for some_dart in self.darts_of_i_cells (2):
            x,y = [],[]
            for dart in self.cell_2 (some_dart): # for 2D maps the orbiting darts of the face are 'sorted'
                x.append (vertices [dart%8,0] + (dart // 8) %  self.n_cols)
                y.append (vertices [dart%8,1] + (dart // 8) // self.n_cols)
                if number_darts:
                    self._plot_dart_no (dart)
            x.append (vertices [some_dart%8,0] + (some_dart // 8) %  self.n_cols)
            y.append (vertices [some_dart%8,1] + (some_dart // 8) // self.n_cols)

            plt.fill (x, y, alpha=.2)
            plt.plot (x,y)
            plt.scatter (x[1::2],y[1::2],marker='+',color='k')
            plt.scatter (x[0::2],y[0::2],marker='o',color='k')

        plt.gca().set_aspect (1)
        plt.xticks ([])  # (np.arange (self.n_cols))
        plt.yticks ([])  # (np.arange (self.n_rows)[::-1])
        plt.ylim (self.n_rows-.5, -.5)
        plt.axis ('off')
        plt.title (self.__str__())

    @classmethod
    def from_shape (cls, R, C, sew = True, bounded = True):

        """Constructs grid-like gmap from number rows and columns

        Args:
            R: number of rows
            C: number of columns
            sew: sew the pixels together (default) or not?
            bounded: set to False to add the outer boundary

        Returns:
            2-gMap representing a pixel array

        """
        def _swap2 (A,  r1,c1,i1,  r2,c2,i2):
            """swap helper to 2-sew darts"""
            tmp = A [r1,c1,i1,2].copy()
            A [r1,c1,i1,2] = A [r2,c2,i2,2]
            A [r2,c2,i2,2] = tmp

        def _iter_boundary (R,C):
            """counter-clockwise boundary iteration around the block darts"""
            c = 0
            for r in range (R):
                yield 8*(r*C+c) + 7
                yield 8*(r*C+c) + 6
            r = R-1
            for c in range(C):
                yield 8*(r*C+c) + 5
                yield 8*(r*C+c) + 4
            c = C-1
            for r in range (R-1,-1,-1):
                yield 8*(r*C+c) + 3
                yield 8*(r*C+c) + 2
            r = 0
            for c in range (C-1,-1,-1):
                yield 8*(r*C+c) + 1
                yield 8*(r*C+c) + 0

        # set the members
        cls._nR = R
        cls._nC = C

        # compute the total number of darts
        n_all_darts = 8*R*C + (not bounded)*4*(R+C)

        alphas_all   = np.full ((3, n_all_darts), fill_value=-1, dtype=np.int64)   #  TODO dtype can be smaller for small images
        alphas_block = alphas_all [:, :8*R*C ] # view at the block part
        alphas_bound = alphas_all [:,  8*R*C:] # view at the outer boundary part

        # create the square by replicating bounded square with increments
        alphas_square = nGmap.from_string (G2_SQUARE_BOUNDED).T
        A = alphas_block.T.reshape ((R,C,8,3)) # rearrange view at the block part
        for r in range (R):
            for c in range (C):
                A [r,c] = alphas_square + 8 * (r*C + c)

        if sew: # 2-sew the squares
            for r in range (R):
                for c in range (C-1):
                    _swap2 (A, r,c,[2,3], r,c+1, [7,6])
            for c in range (C):
                for r in range (R-1):
                    _swap2 (A, r,c,[4,5], r+1, c, [1,0])

        if not bounded: #` add boundary darts
            # set alpha0 to: 1 0 3 2 5 3 ...
            alphas_bound [0,1::2] = np.arange (0,alphas_bound.shape[1],2)
            alphas_bound [0,0::2] = np.arange (1,alphas_bound.shape[1],2)

            # set alpha1 to: L 2 1 4 3 ... 0
            alphas_bound [1,0]      = alphas_bound.shape[1]-1
            alphas_bound [1,1:-1:2] = np.arange (2,alphas_bound.shape[1],2)
            alphas_bound [1,2:-1:2] = np.arange (1,alphas_bound.shape[1]-1,2)
            alphas_bound [1,-1]     = 0

            # add offsets to alpha0 and alpha1 of the boundary block
            alphas_bound[:2] += 8*R*C

            # 2-sew the the darts of the boundary with the darts of the block
            for d_bound,d_block in enumerate (_iter_boundary(R,C)):
                alphas_block [2, d_block] = d_bound + 8*R*C
                alphas_bound [2, d_bound] = d_block

        
        return cls.from_alpha_array (alphas_all)

    @classmethod
    def from_implicit_given_shape(cls, R, C, sew = True, bounded = False):
        """
            This method is useful to have the same set of darts generate by the implicit
            implementation using the Morton code. The basic implementation of the PixelMap
            give us a set of darts where they are sequential and do not follow the bit
            flip logic. Consequently, also the alphas will be wrong without this method.
        """
        m = dict_nGmap(2, D)

        return m


def is_self_adjacent (G,d):
    # returns if face is self touching at dart d
    # 
    if G.a2 (d) == d: return False  # border dart (needed only for bounded faces?)

    e = G.a2 (d) # 2-oposit of d
    
#   return set (G.cell_2 (d)) == set (G.cell_2 (e))   # compares two sets, which is not necessary
#   return                d   in set (G.cell_2 (e))   # TODO: can be done w/o creating the set
    return                d   in      G.cell_2 (e)    # only iteration ;)


def pendant_darts(G):
    for d in G.darts:
        if G.ai(1,d) == G.ai(2,d):
            yield d



#-------------------------------- LabelMap class ----------------------------------------
class LabelMap (PixelMap):
    # _initial_dart_polylines_00 stores start and end coordinates of darts in pixel (0,0)
    _initial_dart_polylines_00 = np.fromstring("""\
        0 1  2 1   2 2  2 2   2 1  0 1   0 0  0 0
        0 0  0 0   0 1  2 1   2 2  2 2   2 1  0 1
        """, sep=' ', dtype=np.float32).reshape(2, 16).T.reshape(8, 2, 2)
    _initial_dart_polylines_00 -= 1
    _initial_dart_polylines_00 *= .95
    _initial_dart_polylines_00 += 1
    _initial_dart_polylines_00 /= 2
    _initial_dart_polylines_00 -= .5

    @classmethod
    def from_labels (cls, labels):
        if type(labels) == str:
            n_lines = len (labels.splitlines())
            labels = np.fromstring (labels, sep=' ', dtype=np.uint8).reshape (n_lines, -1)
        # 'c' is the representation of the current Gmap
        c = cls.from_shape (labels.shape[0], labels.shape[1], bounded=False)
        
        
        '''
            Compunting the following command, I will not have anymore a LabelMap, but with my method
            I will have a dict_Gmap and I will lost all the properties of the LabelMap. Thus,
            my method is not the best option I have, I think...
            c = cls.from_implicit_given_shape(R,C,bounded=False) '''

        #print('c: ',c)
        cls._labels = labels
        #print('cls: ', cls)

        # add drawable polyline for each dart
        c._dart_polyline = {}
        for d in D:
            c._dart_polyline [d] = LabelMap._initial_dart_polylines_00[d % 8].copy()
            c._dart_polyline [d][..., 0] += (d // 8)  % C
            c._dart_polyline [d][..., 1] += (d // 8) // C

        return c

    def plot(self, number_darts=True, image_palette='gray'):
        """Plots the label map.

        image_palette : None to not show the label pixels.
        """
        #self.darts is inehrited from the nGmap class in gmaps.py that generates an incremental sequence of darts.
        # For that reason, I want to swap self.darts with D, that is the set generated by the morton encoding.
        #for d in self.darts:
        for d in D:
            #e = self.a0(d)
            e = alpha_0(d)
            plt.plot   (self._dart_polyline[d][ :,0], self._dart_polyline[d][: ,1],'k-')
            plt.plot ([self._dart_polyline[d][-1,0],self._dart_polyline[e][-1,0]],[self._dart_polyline[d][-1,1],self._dart_polyline[e][-1,1]], 'k-')
            # f = self.a1(d)
            # plt.plot ([self._dart_polyline[d][ 0,0],self._dart_polyline[f][ 0,0]],[self._dart_polyline[d][ 0,1],self._dart_polyline[f][ 0,1]], 'b-')
            if number_darts:
                self._plot_dart_no(d)
            plt.scatter(self._dart_polyline[d][ 0,0], self._dart_polyline[d][ 0,1], c='k')
#             plt.scatter(self._dart_polyline[d][-1,0], self._dart_polyline[d][-1,1], marker='+')

        if image_palette:
            plt.imshow (self.labels, alpha=0.5, cmap=image_palette)

        plt.gca().set_aspect (1)
        plt.xticks ([])  # (np.arange (self.n_cols))
        plt.yticks ([])  # (np.arange (self.n_rows)[::-1])
        plt.ylim (self.n_rows-.5, -.5)
        plt.axis ('off')
        plt.title (self.__str__())

    @property
    def labels(self):
        return self._labels

    def value (self,d):
        """Returns label value for given dart"""
        p = d // 8
        return self.labels [p // self.n_cols, p % self.n_cols]

    def remove_edges (self):
        # TODO edge removal causes skips in the outer loop if used w/i list() ???
        for d in list (self.darts_of_i_cells (1)):          # d ... some dart while iterating over all edges
            e = self.a2(d)                           # e ... dart of the oposit face

            if d == e:                               # boundary edge
                logging.debug ('Skipping: belongs to boundary.')
                continue
            if d == self.a1(e):                      # dangling dart
                logging.debug (f'{d} : pending')
#                 logging.info (d)
                self.remove_edge(d)
                continue
            if d == self.a0 (self.a1 (self.a0 (e))): # dangling edge
                logging.debug (f'{d} : pending')
#                 logging.info (d)
                self.remove_edge(d)
                continue
            if d in self.cell_2 (e):                 # bridge (self-touching face)
                logging.debug (f'Skipping bridge at {d}')
                continue
            if (self.value(d) == self.value(e)).all():       # identical colour in CCL
                logging.debug  (f'{d} : low-contrast')
#                 logging.info (d)
                self.remove_edge(d)
                continue
            logging.debug (f'Skipping: contrast edge at {d}')

    def remove_vertex (self,d):
        if not self.is_i_removable(0,d):
            return
        for d in self.cell_0 (d):
            e = self.a0 (d)
            self._dart_polyline [e] = np.vstack ((self._dart_polyline [e], self._dart_polyline [d][::-1]))
        super().remove_vertex(d)

    # TODO vetrices removal causes skips in darts in the outer loop if used w/i list() ???
    def remove_vertices (self):
        for d in list (self.darts_of_i_cells (0)):      # d ... some dart while iterating over all vertices
            try:
                self.remove_vertex (d)                  # the degree is checked inside
                logging.debug (f'{d} removed')
            except:
                logging.debug (f'{d} NOT removable')




class custom_LM(dict_nGmap):

    def __init__(self):
        self.labels = {}
        self.m = dict_nGmap(2)

    def generate_chessboard_labels(self):

        cnt = 0
        for x in self.m.all_i_cells(2):
            
            #print(list(x))
            for i in x:
                if cnt == 0:
                    self.labels[i] = 'red'
                elif cnt % 2 == 0:
                    self.labels[i] = 'white'
                else:
                    self.labels[i] = 'black'
            
            cnt += 1
        
        """
            I can distinguish three cases:
            cont = 0 -> bounding faces -> brown
            cont = odd values  -> B
            cont = even values -> W
        """
