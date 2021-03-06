import ast
import math
from os import listdir
from os.path import join, isfile
from pathlib import Path
import random

import pandas as pd
from itertools import combinations


def progress(numerator,denominator, width=30):
    """
    simple progress meter display
    :param percent:
    :param width:
    :return:
    """
    left = int(width * numerator/denominator)
    right = width - left
    print('\r',numerator,'/',denominator,' [', '#' * left, ' ' * right, ']', f' {(numerator/denominator)*100:.0f}%', sep='', end='', flush=True)
def ncr(n, r):
    f = math.factorial
    return f(n) // f(r) // f(n - r)

def createFullAthleteNetwork():
    """
    For each segment in Data/Master/Segments get all combinations of athletes and add 1 to weight
    converts dictionary of (source,target) to df with weight
    saves df to Data/Networks/fullNetwork
    :return: network df
    """
    base_path = Path(__file__).parent
    file_path = (base_path / "../Data/Master/Segments").resolve()
    currentSegments = sorted([int(f[:-4]) for f in listdir(file_path) if isfile(join(file_path, f))])
    print("Total segments: ",len(currentSegments))
    network={}
    count=0
    for segment in currentSegments:
        count+=1
        file_path = (base_path / f"../Data/Master/Segments/{segment}.csv").resolve()
        athlete_list = combinations(pd.read_csv(file_path)['athlete_id'], 2)
        for i in list(athlete_list):
            if i in network.keys():
                network[i] += 1
            elif i[::-1] in network.keys():
                network[i[::-1]] += 1
            else:
                network[i] = 1
        progress(count,len(currentSegments))
    print()
    network = pd.Series(network).reset_index()
    print("Network size: ",len(network.index))

    network.columns = ["Source", "Target", "weight"]
    network.to_csv(f"../Data/Networks/fullNetwork.csv",index=False)
    return network
def createFullSegmentNetwork():
    """
    For each segment in Data/Master/Segments

    :return: network df
    """
    base_path = Path(__file__).parent
    file_path = (base_path / "../Data/Master/Segments").resolve()
    currentSegments = sorted([int(f[:-4]) for f in listdir(file_path) if isfile(join(file_path, f))])
    print("Total segments: ",len(currentSegments))
    network={}
    count=0
    for segment in currentSegments:
        count+=1
        file_path = (base_path / f"../Data/Master/Segments/{segment}.csv").resolve()
        athlete_id=pd.read_csv(file_path)['athlete_id']
        network[segment]=list(athlete_id)

    network = pd.Series(network).reset_index()
    network.columns = ["segment_id", "athlete_list"]
    segment_combinations = combinations(network['segment_id'], 2)
    #print("Segment combinations: ",sum(1 for ignore in segment_combinations))
    networkGraph= {}
    count=0
    numCombinations=ncr(len(network.index),2)
    for idx,i in enumerate(segment_combinations):
        segment1=i[0]
        segment1_athletes=network.loc[network['segment_id'] == segment1]['athlete_list'].tolist()[0]
        segment2 = i[1]

        segment2_athletes = network.loc[network['segment_id'] == segment2]['athlete_list'].tolist()[0]

        #
        union=len(set(segment1_athletes).intersection(segment2_athletes))
        if union>0:
            networkGraph[i]=union
        count+=1
        progress(count,numCombinations)

    networkGraph = pd.Series(networkGraph).reset_index()
    print("Network size: ", len(networkGraph.index))

    networkGraph.columns = ["Source", "Target", "weight"]
    networkGraph.to_csv(f"../Data/Networks/fullNetwork.csv", index=False)

    networkGraph.to_csv(f"../Data/Networks/fullSegmentNetwork.csv",index=False)
    return networkGraph
def getFullAthleteNetwork(new=False):
    """
    Helper to get FullNetwork
    if new=False then look for it in Data/Network else createFullNetwork
    :param new:
    :return:
    """
    base_path = Path(__file__).parent
    if(new):
        return createFullAthleteNetwork()
    else:
        return  pd.read_csv((base_path / f"../Data/Networks/fullNetwork.csv").resolve(),dtype={"Source": 'int32', "Target": 'int32',"weight":'int16'})

def createEgoNetwork(seed, n,visited=None):
    if visited == None:
        visited=[seed]
    else:
        visited.append(seed)
    base_path = Path(__file__).parent
    file_path = (base_path / "../Data/Master/Segments").resolve()
    currentSegments = [int(f[:-4]) for f in listdir(file_path) if isfile(join(file_path, f))]
    network={}
    print("Seed: ",seed)
    neighbors=set()
    for segment in currentSegments:
        file_path = (base_path / f"../Data/Master/Segments/{segment}.csv").resolve()
        segmentDf=pd.read_csv(file_path)

        if(seed in segmentDf['athlete_id'].unique()):
            neighbors.update(set(segmentDf['athlete_id']))

    neighbors.remove(seed)

    neighborCount=0
    neighbors=random.sample(neighbors,10**n)
    for neighbor in neighbors:
        neighborCount+=1
        pair=(seed,neighbor)
        if pair in network.keys():
            network[pair] += 1
        elif pair[::-1] in network.keys():
            network[pair[::-1]] += 1
        else:
            network[pair] = 1

        if n>0 and neighbor not in visited:
            subnet=createEgoNetwork(neighbor,n-1,visited)
            print(subnet)
            for key in subnet.keys():
                if key in network.keys():
                    network[key]+= subnet[key]
                elif key[::-1] in network.keys():
                    network[key[::-1]]+= subnet[key]
                else:
                    network[key] = subnet[key]

            print(f"N:{n} Neighborcount: {neighborCount}/{len(neighbors)}")


    return network

def createEgoNetwork2(network,seed ,n):
    if n==0:
        network = network.query(f'Source=={seed} or Target=={seed}')
        network = network.sample(len(network.index) // 10)
        return network
    else:
        oldNetwork=network.copy(deep=True)
        network = network.query(f'Source=={seed} or Target=={seed}')
        network = network.sample(len(network.index) // 10)
        oldNetwork = oldNetwork.drop(network.index)
        seeds = set(network['Target'].unique().tolist() + network['Source'].unique().tolist())
        seeds.remove(seed)
        for idx,newSeed in enumerate(seeds):
            print(f"N: {n} Seed num{idx}/{len(seeds)}")
            network=network.append(createEgoNetwork2(oldNetwork, newSeed, n-1))
        return network

def getEgoNetwork(seed,n,new=False):
    base_path = Path(__file__).parent
    if (new):
        network = getFullAthleteNetwork()
        network.info(verbose=False, memory_usage="deep")
        network=createEgoNetwork2(network,seed,n)
        # network = pd.Series(network).reset_index()
        # print("Network size: ", len(network.index))
        #
        # network.columns = ["Source", "Target", "weight"]
        network.to_csv(f"../Data/Networks/{seed}_egoNetwork_{n}.csv",index=False)
        return network
    else:
        return pd.read_csv((base_path / f"../Data/Networks/{seed}_egoNetwork_{n}.csv").resolve())

def validateData():
    """
    Just make sure no files are empty
    :return:
    """
    base_path = Path(__file__).parent
    file_path = (base_path / "../Data/Master/Segments").resolve()
    currentSegments = [int(f[:-4]) for f in listdir(file_path) if isfile(join(file_path, f))]

    i=0

    for index,segment in enumerate(currentSegments):
        file_path = (base_path / f"../Data/Master/Segments/{segment}.csv").resolve()
        segmentDf=pd.read_csv(file_path)
        i+=len(segmentDf.index)>1
    print(i/len(currentSegments))

def main():
    createFullSegmentNetwork()
    #validateData()
    #getEgoNetwork(45406272,1,True)
    #network=getFullNetwork(True)
    # print(network)
    print()
if __name__ == '__main__':
    main()
