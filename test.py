import os
import sys
import torch
import numpy as np
from random import shuffle
import matplotlib.pyplot as plt
from emetrics import get_aupr, get_cindex, get_rm2, get_ci, get_mse, get_rmse, get_pearson, get_spearman
from utils import *
from scipy import stats


def predicting(model, device, loader):
    model.eval()
    total_preds = torch.Tensor()
    total_labels = torch.Tensor()
    print('Make prediction for {} samples...'.format(len(loader.dataset)))
    with torch.no_grad():
        for data in loader:
            data_mol = data[0].to(device)
            data_pro = data[1].to(device)
            # data = data.to(device)
            output = model(data_mol, data_pro)
            total_preds = torch.cat((total_preds, output.cpu()), 0)
            total_labels = torch.cat((total_labels, data_mol.y.view(-1, 1).cpu()), 0)
    return total_labels.numpy().flatten(), total_preds.numpy().flatten()


def load_model(model_path):
    model = torch.load(model_path)
    return model


def calculate_metrics(Y, P, fold=0, dataset="davis"):
    # aupr = get_aupr(Y, P)
    cindex = get_cindex(Y, P)
    cindex2 = get_ci(Y, P)
    rm2 = get_rm2(Y, P)
    mse = get_mse(Y, P)
    pearson = get_pearson(Y, P)
    spearman = get_spearman(Y, P)
    rmse = get_rmse(Y, P)

    print("metrics for ", dataset, "fold:", fold)
    # print("aupr:", aupr)
    print("cindex:", cindex)
    print("cindex2", cindex2)
    print("rm2:", rm2)
    print("mse:", mse)
    print("pearson", pearson)

    result_file_name = "results/result_" + model_st + "_" + dataset + "_" + str(fold) + ".txt"
    result_str = ""
    result_str += dataset + "fold" + str(fold) + '\r\n'
    result_str += "rmse:" + str(rmse) + " " + " mse:" + str(mse) + " " + " pearson:" + str(
        pearson) + " " + "spearman:" + str(spearman) + " " + "ci:" + str(cindex2) + " " + "rm2:" + str(rm2)
    print(result_str)
    open(result_file_name, "w").writelines(result_str)


def plot_density(Y, P, fold=0, dataset="davis"):
    plt.figure(figsize=(10, 5))
    plt.grid(linestyle="--")
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.scatter(P, Y, color='blue', s=40)
    plt.title("fold " + str(fold + 1), fontsize=30, fontweight='bold')
    plt.xlabel("predicted", fontsize=30, fontweight='bold')
    plt.ylabel("measured", fontsize=30, fontweight='bold')
    # plt.xlim(0, 21)
    # plt.ylim(0, 21)
    if dataset == "davis":
        plt.plot([5, 11], [5, 11], color="black")
    else:
        plt.plot([6, 16], [6, 16], color="black")
    # plt.legend()
    plt.legend(loc=0, numpoints=1)
    leg = plt.gca().get_legend()
    ltext = leg.get_texts()
    plt.setp(ltext, fontsize=12, fontweight='bold')
    plt.savefig(os.path.join('results', dataset + '_' + str(fold) + '.png'), dpi=500, bbox_inches='tight')


if __name__ == '__main__':
    import torch
    from gnn import GNNNet
    from torch_geometric.data import Batch
    from utils import *
    from create_data import create_dataset

    dataset = ["davis", "kiba"][int(sys.argv[1])]  # dataset selection
    model_st = GNNNet.__name__

    cuda_name = ["cuda:0", "cuda:1", "cuda:2", "cuda:3"][int(sys.argv[2])] # gpu selection
    print("cuda_name:", cuda_name)

    fold = [0, 1, 2, 3, 4][int(sys.argv[3])] # fold for the 5-fold 
    # print(int(sys.argv[3]))
    print("fold", fold)
    TEST_BATCH_SIZE = 512
    models_dir = "models"
    results_dir = "results"

    _, _, test_data = create_dataset(dataset, fold)
    test_loader = torch.utils.data.DataLoader(test_data, batch_size=TEST_BATCH_SIZE, shuffle=False,
                                              collate_fn=collate)
    # training the model
    model_file_name = "models/model_" + model_st + "_" + dataset + "_" + str(fold) + ".model"
    # model_state_name = 'models/model_' + model_st + '_' + dataset + "_" + str(fold) + '.model'
    device = torch.device(cuda_name if torch.cuda.is_available() else "cpu")
    result_file_name = "results/result_" + model_st + "_" + dataset + "_" + str(fold) + ".txt"
    model = torch.load(model_file_name)
    Y, P = predicting(model, device, test_loader)
    calculate_metrics(Y, P, fold, dataset)
    plot_density(Y, P, fold, dataset)