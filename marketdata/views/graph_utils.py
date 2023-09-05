import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def call_payoff(x, K, P, side, size=1, **kwargs):
    
    if side == 'b':
        return np.maximum((x - K)*size, 0) - P*size
    elif side == 's':
        return np.minimum((K - x)*size, 0) + P*size
    else:
        raise Exception("Side must be b or s")
        
def put_payoff(x, K, P, side, size=1, **kwargs):
    
    if side == 'b':
        return np.maximum((K - x)*size, 0) - P*size
    elif side == 's':
        return np.minimum((x - K)*size, 0) + P*size
    else:
        raise Exception("Side must be b or s")
        
def underlying(x, S, side, size=1, **kwargs):
    
    if side == 'b':
        return (x - S)*size
    elif side == 's':
        return (S - x)*size
    else:
        raise Exception("Side must be b or s")

        
payoff_func = {
    'c': call_payoff,
    'p': put_payoff,
    'u': underlying
}
        
label_map = {
    'c': 'Call',
    'p': 'Put',
    'u': 'Underlying',
    'b': 'Long',
    's': 'Short',
}
        
        
def multi_plotter(spot, op_list, spot_range=20):
    # op_list args:
    #     type=c,p,u
    #     side=b,s
    #     price=<float>
    #     [size]=<int>  (default: 1)
    #     [strike]=<float>  (for put/call)

    x=spot*np.arange(100-spot_range,101+spot_range,0.01)/100
    y0=np.zeros_like(x)         
    
    y_list=[]
    for op in op_list:
        inst_type = str.lower(op['type'])
        side = str.lower(op['side'])
        
        K = op.get('strike', None)
        P = op['price']
        size = op.get('size', 1)
        
        payoff_calculator = payoff_func[inst_type]
        y_list.append(payoff_calculator(x=x, K=K, P=P, S=P, side=side, size=size))
    

    def plotter():
        y=0
        plt.figure(figsize=(10,6))
        for i in range (len(op_list)):
            op = op_list[i]
            inst_type = str.lower(op['type'])
            side = str.lower(op['side'])

            K = op.get('strike', '')
            if K:
                K = '-' + str(K)
            P = op['price']
            size = op.get('size', 1)
            
            
            label = f'{label_map[side]} {label_map[inst_type]}{K} {size} @ ${P:>6.2f}'
            sns.lineplot(x=x, y=y_list[i], label=label, alpha=0.5)
            y+=np.array(y_list[i])
        
        sns.lineplot(x=x, y=y, label='combined', alpha=1, color='k')
        plt.axhline(color='k', linestyle='--')
        plt.axvline(x=spot, color='r', linestyle='--', label='spot price')
        plt.legend()
        plt.legend(loc='upper right')
        plt.fill_between(x, y, 0, alpha=0.2, where=y>y0, facecolor='green', interpolate=True)
        plt.fill_between(x, y, 0, alpha=0.2, where=y<y0, facecolor='red', interpolate=True)
        plt.tight_layout()

        return plt.gcf()

    return plotter()


def get_plots(spot, op_list, spot_range=20):
    # op_list args:
    #     type=c,p,u
    #     side=b,s
    #     price=<float>
    #     [size]=<int>  (default: 1)
    #     [strike]=<float>  (for put/call)

    x=spot*np.arange(100-spot_range,101+spot_range,0.01)/100
    y0=np.zeros_like(x)         
    
    y_list = []
    y_labels = []
    for op in op_list:
        inst_type = str.lower(op['type'])
        side = str.lower(op['side'])
        
        K = op.get('strike', None)
        P = op['price']
        size = op.get('size', 1)
        
        payoff_calculator = payoff_func[inst_type]
        y_list.append(payoff_calculator(x=x, K=K, P=P, S=P, side=side, size=size))
        y_labels.append(f'{label_map[side]} {label_map[inst_type]}{K} {size} @ ${P:.2f}')
    combined = sum(y_list)

    return x, y_list, y_labels, combined