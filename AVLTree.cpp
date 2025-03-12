#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <limits>
#include <cmath>

using namespace std;

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

int main() {
    string filename;
    cout << "txt file name: ";
    cin >> filename;
    AVLNode* root = buildAVLTree(filename);

    if (!root) return 1;

    long long query_timecode;
    cout << "The timecode to be looked up: ";
    cin >> query_timecode;

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
