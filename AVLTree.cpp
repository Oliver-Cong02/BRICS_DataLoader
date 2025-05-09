#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <limits>
#include <cmath>
#include <cstring> 
#include <filesystem>  

using namespace std;
using namespace filesystem;

// AVL tree node definition
struct AVLNode {
    long long timecode;
    string frameidx;
    AVLNode* left;
    AVLNode* right;
    int height;

    AVLNode(long long t, const string& idx)
        : timecode(t), frameidx(idx), left(nullptr), right(nullptr), height(1) {}
};

// Get the height of a node
int getHeight(AVLNode* node) {
    return node ? node->height : 0;
}

// Get the balance factor of a node
int getBalanceFactor(AVLNode* node) {
    return node ? getHeight(node->left) - getHeight(node->right) : 0;
}

// Right rotate (used for LL un-balanced)
AVLNode* rotateRight(AVLNode* y) {
    AVLNode* x = y->left;
    AVLNode* T2 = x->right;

    x->right = y;
    y->left = T2;

    y->height = max(getHeight(y->left), getHeight(y->right)) + 1;
    x->height = max(getHeight(x->left), getHeight(x->right)) + 1;

    return x;
}

// Left rotate (used for RR un-balanced)
AVLNode* rotateLeft(AVLNode* x) {
    AVLNode* y = x->right;
    AVLNode* T2 = y->left;

    y->left = x;
    x->right = T2;

    x->height = max(getHeight(x->left), getHeight(x->right)) + 1;
    y->height = max(getHeight(y->left), getHeight(y->right)) + 1;

    return y;
}

// insert a new node into AVL tree and balance the tree
AVLNode* insert(AVLNode* root, long long timecode, const string& frameidx) {
    if (!root) return new AVLNode(timecode, frameidx);

    if (timecode < root->timecode)
        root->left = insert(root->left, timecode, frameidx);
    else if (timecode > root->timecode)
        root->right = insert(root->right, timecode, frameidx);
    else
        return root; // Do not insert if timecode already exists 

    // update height of this ancestor node
    root->height = 1 + max(getHeight(root->left), getHeight(root->right));

    // Get the balance factor of this node
    int balance = getBalanceFactor(root);

    // LL un-balanced (Right rotate)
    if (balance > 1 && timecode < root->left->timecode)
        return rotateRight(root);

    // RR un-balanced (Left rotate)
    if (balance < -1 && timecode > root->right->timecode)
        return rotateLeft(root);

    // LR un-balanced (First left rotate then right rotate)
    if (balance > 1 && timecode > root->left->timecode) {
        root->left = rotateLeft(root->left);
        return rotateRight(root);
    }

    // RL un-balanced (First right rotate then left rotate)
    if (balance < -1 && timecode < root->right->timecode) {
        root->right = rotateRight(root->right);
        return rotateLeft(root);
    }

    return root;
}

AVLNode* findClosest(AVLNode* root, long long target, long long threshold=1000) {
    AVLNode* closest = nullptr;
    long long minDiff = numeric_limits<long long>::max();

    while (root) {
        long long diff = abs(root->timecode - target);
        if (diff < minDiff) {
            minDiff = diff;
            closest = root;
        }
        if (target < root->timecode)
            root = root->left;
        else
            root = root->right;
    }

    // Check if the closest found timecode is within the threshold
    if (closest && minDiff > threshold) {
        return nullptr;  // No frame found within the threshold
    }

    return closest;
}

// Read txt file and build AVL Tree
AVLNode* buildAVLTree(const string& filename) {
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "Can not open file: " << filename << endl;
        return nullptr;
    }

    AVLNode* root = nullptr;
    string line;

    while (getline(file, line)) {
        istringstream iss(line);
        string prefix, timecode_str, frameidx;
        if (getline(iss, prefix, '_') &&
            getline(iss, timecode_str, '_') &&
            getline(iss, frameidx)) 
        {
            long long timecode = stoll(timecode_str);
            root = insert(root, timecode, frameidx);
        }
    }

    file.close();
    return root;
}

// modify the serialization related functions
void serializeHelper(AVLNode* root, ofstream& outFile) {
    if (!root) {
        char isNull = 0;
        outFile.write(&isNull, sizeof(char));
        return;
    }
    
    char isNull = 1;
    outFile.write(&isNull, sizeof(char));
    
    // write timecode
    outFile.write(reinterpret_cast<char*>(&root->timecode), sizeof(long long));
    
    // write the length and content of frameidx
    size_t len = root->frameidx.length();
    outFile.write(reinterpret_cast<char*>(&len), sizeof(size_t));
    outFile.write(root->frameidx.c_str(), len);
    
    serializeHelper(root->left, outFile);
    serializeHelper(root->right, outFile);
}

// add file name processing function
string getBaseFileName(const string& filename) {
    // 先找到最后一个路径分隔符
    size_t lastSlash = filename.find_last_of("/\\");
    string onlyFileName = (lastSlash == string::npos) ? filename : filename.substr(lastSlash + 1);
    
    // 再去掉扩展名
    size_t lastDot = onlyFileName.find_last_of(".");
    if (lastDot != string::npos) {
        return onlyFileName.substr(0, lastDot);
    }
    return onlyFileName;
}

void serialize(AVLNode* root, const string& filename, const string& save_dir) {
    string baseFileName = getBaseFileName(filename);
    
    // 确保保存目录存在
    path dir_path(save_dir);
    if (!exists(dir_path)) {
        create_directories(dir_path);
    }
    
    path full_path = dir_path / (baseFileName + ".bin");
    ofstream outFile(full_path, ios::binary);
    if (!outFile.is_open()) {
        cerr << "Unable to create binary file: " << full_path << endl;
        return;
    }
    serializeHelper(root, outFile);
    outFile.close();
}

AVLNode* deserializeHelper(ifstream& inFile) {
    char isNull;
    inFile.read(&isNull, sizeof(char));
    
    if (!isNull || inFile.eof()) return nullptr;
    
    // read timecode
    long long timecode;
    inFile.read(reinterpret_cast<char*>(&timecode), sizeof(long long));
    
    // read frameidx
    size_t len;
    inFile.read(reinterpret_cast<char*>(&len), sizeof(size_t));
    string frameidx(len, '\0');
    inFile.read(&frameidx[0], len);
    
    AVLNode* node = new AVLNode(timecode, frameidx);
    node->left = deserializeHelper(inFile);
    node->right = deserializeHelper(inFile);
    
    node->height = 1 + max(getHeight(node->left), getHeight(node->right));
    return node;
}

AVLNode* deserialize(const string& filename, const string& save_dir) {
    string baseFileName = getBaseFileName(filename);
    path full_path = path(save_dir) / (baseFileName + ".bin");
    
    ifstream inFile(full_path, ios::binary);
    if (!inFile.is_open()) {
        return nullptr;
    }
    
    AVLNode* root = deserializeHelper(inFile);
    inFile.close();
    return root;
}

int main() {
    string filename;
    cout << "file name (.txt or .bin): ";
    getline(cin, filename);
    
    AVLNode* root = nullptr;
    string save_dir;
    
    // check if it is a bin file
    if (filename.substr(filename.length() - 4) == ".bin") {
        // if it is a bin file, load it directly
        size_t lastSlash = filename.find_last_of("/\\");
        save_dir = (lastSlash != string::npos) ? filename.substr(0, lastSlash) : ".";
        root = deserialize(filename, save_dir);
        if (!root) {
            cout << "Unable to load tree from binary file!" << endl;
            return 1;
        }
    } else {
        // if it is a txt file, need to save directory
        cout << "tree save directory: ";
        getline(cin, save_dir);
        
        root = deserialize(filename, save_dir);
        if (!root) {
            cout << "No saved tree found, building new tree from txt file..." << endl;
            root = buildAVLTree(filename);
            if (root) {
                cout << "Saving tree to binary file..." << endl;
                serialize(root, filename, save_dir);
            }
        } else {
            cout << "Tree loaded from saved binary file..." << endl;
        }
    }

    if (!root) {
        cout << "Unable to create or load tree!" << endl;
        return 1;
    }

    string timecode_str;
    cout << "The timecode to be looked up (0 for only saving AVLtree binary file): ";
    getline(cin, timecode_str);
    long long query_timecode = stoll(timecode_str);

    if (query_timecode == 0) {
        if (filename.substr(filename.length() - 4) != ".bin") {
            path full_path = path(save_dir) / (getBaseFileName(filename) + ".bin");
            cout << "Done for saving to " << full_path << endl;
        }
        return 0;
    }

    long long threshold;
    cout << "Threshold: ";
    cin >> threshold;

    AVLNode* closest = findClosest(root, query_timecode, threshold);
    if (closest) {
        cout << "Nearest Timecode: " << closest->timecode << ", frameidx: " << closest->frameidx << endl;
        cout << "line in txt file: frame_" << closest->timecode << "_" << closest->frameidx << endl;
    } else {
        cout << "No Frame Found!" << endl;
    }

    return 0;
}
